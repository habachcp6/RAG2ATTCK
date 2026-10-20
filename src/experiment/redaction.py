"""Secret sanitization and redaction for error messages, journals, and logs.

Ensures no API keys, Authorization headers, Bearer tokens, or credentials leak
into persisted files.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_SECRET_PATTERNS = [
    # Authorization: Bearer <token>
    (re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{6,}", re.IGNORECASE), "[REDACTED_BEARER_TOKEN]"),
    (
        re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9_\-\.]{6,}", re.IGNORECASE),
        "[REDACTED_BEARER_TOKEN]",
    ),
    # OpenAI sk- keys
    (re.compile(r"sk-[A-Za-z0-9_\-\.]{8,}", re.IGNORECASE), "[REDACTED_OPENAI_KEY]"),
    # Common token/key assignments: api_key=..., api-key: ..., token=..., secret=...
    (
        re.compile(
            r"(?i)(api[_-]?key|secret|token|password|auth_token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{6,}['\"]?"
        ),
        "[REDACTED_CREDENTIAL]",
    ),
]


def sanitize_secrets(text: str | None, *, extra_tokens: Sequence[str] = ()) -> str | None:
    """Sanitize secret patterns and explicit tokens from text.

    FAIL-CLOSED: returns '[REDACTION_FAILED]' if sanitization encounters any unhandled error.
    """
    if text is None:
        return None
    try:
        result = str(text)

        # Redact explicit tokens first
        for token in extra_tokens:
            if token and len(str(token).strip()) >= 4:
                result = result.replace(str(token).strip(), "[REDACTED_SECRET]")

        # Redact regex patterns
        for pat, replacement in _SECRET_PATTERNS:
            result = pat.sub(replacement, result)

        return result
    except Exception:
        return "[REDACTION_FAILED]"
