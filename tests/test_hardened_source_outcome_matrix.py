"""FU-013 typed source outcomes with offline fixtures and loopback canaries."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

import pytest

from lib import health, http, pipeline, schema


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "tests" / "fixtures" / "hardened-source-outcome-matrix.json"
MATRIX = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
SOURCES = MATRIX["sources"]
CASES = MATRIX["failure_cases"]


def _item(source: str) -> schema.SourceItem:
    return schema.SourceItem(
        item_id=f"{source}-1",
        source=source,
        title="fixture item",
        body="fixture body",
        url="https://example.invalid/item",
    )


def test_matrix_covers_every_runtime_retrieval_source():
    expected = set(pipeline.MOCK_AVAILABLE_SOURCES) | {"stocktwits"}
    assert MATRIX["schema_version"] == "last30days-source-outcome-matrix/v1"
    assert len(SOURCES) == len(set(SOURCES))
    assert set(SOURCES) == expected


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_every_source_maps_each_failure_class_without_clean_empty_laundering(source, case):
    artifact = pipeline._result_outcome_artifact(source, {"error": case["message"]})
    outcome = artifact["_source_outcome"]
    assert outcome["state"] == case["expected"]
    assert outcome["state"] != schema.NO_RESULTS
    assert outcome["attempted"] is True


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_every_source_preserves_items_as_typed_partial_coverage(source, case):
    bundle = schema.RetrievalBundle()
    bundle.mark_attempted(source)
    bundle.add_items("primary", source, [_item(source)])
    bundle.record_failure(source, case["expected"], case["message"])
    outcome = bundle.source_status[source]
    expected = schema.AUTH_FAILED if case["expected"] == schema.AUTH_FAILED else schema.PARTIAL
    assert outcome.state == expected
    assert outcome.items_returned == 1
    assert outcome.detail == case["message"]
    assert outcome.fix_hint == "doctor"


@pytest.mark.parametrize("source", SOURCES)
def test_every_source_distinguishes_clean_no_results(source):
    bundle = schema.RetrievalBundle()
    bundle.mark_attempted(source)
    assert bundle.source_status[source].state == schema.NO_RESULTS
    assert source not in bundle.errors_by_source


def test_local_permission_failure_is_typed_error_not_no_results():
    state, attempted = pipeline._classify_source_failure(
        PermissionError("Permission denied reading local source")
    )
    assert state == health.ERROR
    assert attempted is True


class _CanaryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/invalid-json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"not-json")
            return
        if self.path == "/slow":
            time.sleep(0.2)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        status = int(self.path.removeprefix("/"))
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": status}).encode("utf-8"))

    def log_message(self, _format, *_args):
        return


@pytest.fixture
def local_canary():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _CanaryHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, schema.RATE_LIMITED),
        (401, schema.AUTH_FAILED),
        (402, schema.PAYMENT_REQUIRED),
        (403, schema.AUTH_FAILED),
    ],
)
def test_loopback_canary_classifies_real_http_status(local_canary, status, expected):
    with pytest.raises(http.HTTPError) as caught:
        http.get(
            f"{local_canary}/{status}",
            retries=1,
            max_429_retries=0,
            bypass_proxy=True,
        )
    assert caught.value.status_code == status
    assert caught.value.outcome_state == expected


def test_loopback_canary_classifies_invalid_json(local_canary):
    with pytest.raises(http.HTTPError) as caught:
        http.get(
            f"{local_canary}/invalid-json",
            retries=1,
            bypass_proxy=True,
        )
    assert caught.value.outcome_state == schema.SCHEMA_DRIFT


def test_loopback_canary_classifies_timeout(local_canary):
    with pytest.raises(http.HTTPError) as caught:
        http.get(
            f"{local_canary}/slow",
            timeout=0.02,
            retries=1,
            bypass_proxy=True,
        )
    assert caught.value.outcome_state == health.TIMEOUT
