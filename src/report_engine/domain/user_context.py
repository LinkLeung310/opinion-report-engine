"""User-supplied context kept separate from verified facts and source evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VerificationStatus(StrEnum):
    """Whether the report engine independently verified a context value."""

    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class UserContext:
    """Normalized user prose with explicit provenance and verification status."""

    key: str
    text: str
    source_id: str
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.text.strip() or not self.source_id.strip():
            raise ValueError("User context fields cannot be blank")
        if self.text != self.text.strip():
            raise ValueError("User context text must be normalized")
        if self.verification_status is not VerificationStatus.UNVERIFIED:
            raise ValueError("User context must remain explicitly unverified")

    @property
    def markdown_safe_text(self) -> str:
        """Render the normalized text literally in Markdown, without active markup."""

        replacements = str.maketrans(
            {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                "!": "&#33;",
                "[": "&#91;",
                "]": "&#93;",
                "*": "&#42;",
                "_": "&#95;",
                "`": "&#96;",
                "\\": "&#92;",
                "~": "&#126;",
            }
        )
        return self.text.translate(replacements)
