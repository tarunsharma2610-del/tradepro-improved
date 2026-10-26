"""Conservative text extractor for Upstox contract-note line items.

This is an evidence-extraction helper only. It does not decide the GST base,
approve a tariff, infer missing zeroes, or promote source values into accounting.
Input must be text extracted from a document whose original bytes/hash and page
locations are retained by the caller. PDF layouts vary; ambiguous/missing fields
must be reviewed rather than guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


AMOUNT = r"(?:₹\s*)?([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)"
_SEGMENT_PATTERNS = (
    ("NSE-EQ", re.compile(r"\bNSE\s*[-–]\s*EQ\b", re.IGNORECASE)),
    ("NSE-F&O", re.compile(r"\bNSE\s*[-–]\s*(?:F\s*&\s*O|FO)\b", re.IGNORECASE)),
    ("NSE-CD", re.compile(r"\bNSE\s*[-–]\s*(?:CD|CUR)\b", re.IGNORECASE)),
    ("MCX", re.compile(r"\bMCX\b", re.IGNORECASE)),
)

# Match known labels only. Preserve the exact matched source line for reviewer
# display; these aliases are extraction hints, not legal tax classifications.
_COMPONENT_PATTERNS = {
    "brokerage": re.compile(rf"^\s*brokerage(?:\s+charges?)?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "transaction_charges": re.compile(rf"^\s*(?:exchange\s+)?(?:txn|transaction)\s+charges?(?:\s+\([^)]*\))?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "exchange_charges": re.compile(rf"^\s*exchange\s+charges?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "sebi_charges": re.compile(rf"^\s*SEBI\s+(?:turnover\s+)?fees?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "ipft": re.compile(rf"^\s*(?:NSE\s+)?IPFT\s+(?:charges?|contribution|fee)?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "demat_transaction_charges": re.compile(rf"^\s*(?:DP|demat)(?:\s+transaction)?\s+charges?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "clearing_charges": re.compile(rf"^\s*clearing(?:\s+member)?\s+charges?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "stt": re.compile(rf"^\s*(?:STT|securities\s+transaction\s+tax)\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "stamp_duty": re.compile(rf"^\s*stamp\s+duty\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "gst_cgst": re.compile(rf"^\s*CGST\s*(?:@\s*9\s*%)?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "gst_sgst": re.compile(rf"^\s*SGST\s*(?:@\s*9\s*%)?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
    "gst_igst": re.compile(rf"^\s*IGST\s*(?:@\s*18\s*%)?\s*[:\-]?\s*{AMOUNT}\s*$", re.IGNORECASE),
}


@dataclass(frozen=True)
class ExtractedLineItem:
    component: str
    amount: Decimal
    source_line: str
    line_number: int


@dataclass(frozen=True)
class ContractNoteExtraction:
    segments: tuple[str, ...]
    line_items: tuple[ExtractedLineItem, ...]
    ambiguous_components: tuple[str, ...]
    unmapped_candidate_lines: tuple[tuple[int, str], ...]


def _parse_amount(raw: str) -> Decimal:
    try:
        value = Decimal(raw.replace(",", ""))
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError("Extracted amount is not a valid decimal.") from exc
    if not value.is_finite() or value < 0 or value != value.quantize(Decimal("0.01")):
        raise ValueError("Extracted amount must be a finite, nonnegative INR paise value.")
    return value


def extract_upstox_contract_note_text(text: str) -> ContractNoteExtraction:
    """Extract recognized line items while retaining ambiguity for human review.

    Duplicate occurrences are retained and their component names are flagged in
    ambiguous_components; they are never silently summed or overwritten.
    Unknown lines that look charge/tax related are returned for review.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Non-empty contract-note text is required.")

    segments = tuple(name for name, pattern in _SEGMENT_PATTERNS if pattern.search(text))
    items: list[ExtractedLineItem] = []
    counts: dict[str, int] = {}
    unmapped: list[tuple[int, str]] = []

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        matched = False
        for component, pattern in _COMPONENT_PATTERNS.items():
            match = pattern.fullmatch(line)
            if match:
                try:
                    amount = _parse_amount(match.group(1))
                except ValueError:
                    # Keep malformed/negative amounts for review instead of
                    # aborting extraction or treating them as zero.
                    unmapped.append((line_number, raw_line))
                    matched = True
                    break
                items.append(ExtractedLineItem(component, amount, raw_line, line_number))
                counts[component] = counts.get(component, 0) + 1
                matched = True
                break
        if not matched and re.search(r"\b(?:charge|charges|GST|CGST|SGST|IGST|IPFT|SEBI|brokerage|demat|clearing|stamp duty|STT|investor protection|contribution)\b", line, re.IGNORECASE):
            unmapped.append((line_number, raw_line))

    ambiguous = tuple(sorted(component for component, count in counts.items() if count > 1))
    return ContractNoteExtraction(
        segments=segments,
        line_items=tuple(items),
        ambiguous_components=ambiguous,
        unmapped_candidate_lines=tuple(unmapped),
    )
