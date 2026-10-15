"""Canonical handling for untrusted and untrusted-derived text.

All public-source text and all model explanations derived from it cross this
boundary before they are embedded in prompts or rendered into engine-owned
Markdown.  The functions preserve ordinary prose while making structural
control tokens inert and keeping derived explanations bounded.
"""

from __future__ import annotations

import re
import unicodedata


TRUST_LEVEL = "UNTRUSTED_DERIVED"
MAX_EXPLANATION_CHARS = 600

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
_MARKDOWN_FENCE = re.compile(r"(?m)^(\s*)(`{3,}|~{3,})")

# Tolerate spaces, line breaks, common separators, attributes, and full-width
# forms (NFKC-normalized before matching).  Entity-encoded underscores are
# handled separately before ampersands are escaped.
_UNTRUSTED_TAG = re.compile(
    r"<\s*/?\s*untrusted(?:[_\-\s]+)content(?:\s+[^>]*)?\s*/?\s*>",
    re.IGNORECASE,
)
_ENCODED_UNDERSCORE = re.compile(
    r"untrusted\s*(?:&#0*95;|&#x0*5f;)\s*content", re.IGNORECASE
)
_ENCODED_ANGLE = re.compile(
    r"&(?P<entity>lt|gt|#0*60|#x0*3c|#0*62|#x0*3e);", re.IGNORECASE
)

_CONTROL_PHRASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bpass[\s\-\u2013\u2014]+through\s+footer\b", re.IGNORECASE),
        "PASS-THROUGH-FOOTER",
    ),
    (
        re.compile(r"\bevidence\s+for\s+synthesis\b", re.IGNORECASE),
        "EVIDENCE-FOR-SYNTHESIS",
    ),
    (
        re.compile(r"\bsynthesis\s+contract\b", re.IGNORECASE),
        "SYNTHESIS-CONTRACT",
    ),
    (
        re.compile(
            r"\bend\s+of\s+last30days\s+canonical\s+output\b",
            re.IGNORECASE,
        ),
        "END-OF-last30days-CANONICAL-OUTPUT",
    ),
    (
        re.compile(r"\bi(?:'|\u2019)m\s+now\s+an\s+expert\b", re.IGNORECASE),
        "I-am-not-now-an-expert",
    ),
    (
        re.compile(r"\breference\s+selector\b", re.IGNORECASE),
        "REFERENCE-SELECTOR",
    ),
    (
        re.compile(r"\bfake\s+tool\s+call\b", re.IGNORECASE),
        "FAKE-TOOL-CALL",
    ),
    (re.compile(r"\blaw\s+([0-9]+)\b", re.IGNORECASE), r"LAW-\1"),
)


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")
    text = _CONTROL_CHARS.sub("\ufffd", text)
    text = _ZERO_WIDTH.sub("\ufffd", text)
    # Confusables observed in the adversarial corpus.  Restrict the mapping to
    # letters needed by boundary tokens rather than transliterating prose.
    text = text.translate(
        str.maketrans(
            {
                "\u0410": "A",
                "\u0430": "a",
                "\u041e": "O",
                "\u043e": "o",
                "\u0421": "C",
                "\u0441": "c",
            }
        )
    )
    return text


def _defang_structure(text: str) -> str:
    text = _ENCODED_UNDERSCORE.sub("untrusted-content", text)
    text = _UNTRUSTED_TAG.sub(
        lambda match: match.group(0).replace("_", "-"), text
    )
    text = text.replace("<!--", "<!- -").replace("-->", "- ->")
    for pattern, replacement in _CONTROL_PHRASES:
        text = pattern.sub(replacement, text)
    # Prevent angle-bracket entities from being decoded into fresh delimiters
    # while leaving ordinary prose and URL query separators byte-preserved.
    text = _ENCODED_ANGLE.sub(lambda match: f"&amp;{match.group('entity')};", text)
    text = _MARKDOWN_FENCE.sub(
        lambda match: (
            f"{match.group(1)}{match.group(2)[:2]}\u200b{match.group(2)[2:]}"
        ),
        text,
    )
    return text


def sanitize_untrusted_text(
    value: object,
    *,
    limit: int | None = None,
    single_line: bool = False,
) -> str:
    """Return inert text suitable for prompt or Markdown data positions."""

    text = _defang_structure(_normalize(value))
    if single_line:
        text = " ".join(text.split())
    else:
        text = text.strip()
    if limit is not None and len(text) > limit:
        if limit <= 3:
            return text[:limit]
        text = text[: limit - 3].rstrip() + "..."
    return text


def sanitize_untrusted_title(value: object, *, limit: int = 300) -> str:
    """Return a bounded, single-line title that cannot mint structure."""

    return sanitize_untrusted_text(value, limit=limit, single_line=True)


def bounded_untrusted_explanation(
    value: object, *, limit: int = MAX_EXPLANATION_CHARS
) -> str | None:
    """Sanitize a model-derived explanation and bound its rendered size."""

    text = sanitize_untrusted_text(value, limit=limit, single_line=True)
    return text or None


def sanitize_synthesized_markdown(value: object) -> str:
    """Preserve ordinary Markdown while defanging engine-owned control text.

    Synthesized prose is model-derived from untrusted evidence.  It may keep
    headings, emphasis, tables, and links, but it must not mint the HTML
    renderer's footer, evidence, metadata, invitation, or canonical-boundary
    markers.  The canonical sanitizer already neutralizes those marker
    delimiters and phrases without flattening line structure.
    """

    return sanitize_untrusted_text(value)


def fence_untrusted_content(value: object) -> str:
    """Wrap source data with exactly one engine-owned fence."""

    text = sanitize_untrusted_text(value)
    return f"<untrusted_content>\n{text}\n</untrusted_content>"
