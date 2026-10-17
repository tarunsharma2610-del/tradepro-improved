"""
Pure RSS 2.0 parsing and instrument matching, no DB/network — news_service.py
does the fetching and persisting. Tested against real captured content
(see tests/test_news_parsing.py), not a synthetic guess at RSS's shape.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree


@dataclass
class ParsedNewsItem:
    title: str
    link: str
    summary: str | None
    published_at: datetime | None


def parse_rss(xml_content: str) -> list[ParsedNewsItem]:
    """Handles standard RSS 2.0 <channel><item> structure. Ignores any
    namespaced extensions (media:, atom:, etc.) — this only reads
    title/link/description/pubDate, which are never namespaced in RSS 2.0
    itself regardless of what else a feed bolts on."""
    try:
        root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError:
        return []

    items = []
    for item in root.findall(".//item"):
        title = _text(item, "title")
        link = _text(item, "link")
        if not title or not link:
            continue  # not a usable entry — skip rather than guess

        items.append(
            ParsedNewsItem(
                title=title,
                link=link,
                summary=_text(item, "description"),
                published_at=_parse_pubdate(_text(item, "pubDate")),
            )
        )
    return items


def _text(item: ElementTree.Element, tag: str) -> str | None:
    el = item.find(tag)
    if el is None or el.text is None:
        return None
    return el.text.strip() or None


def _parse_pubdate(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None


def match_instruments(text: str, instrument_lookup: dict[str, object]) -> list[object]:
    """`instrument_lookup` maps a matchable string (trading_symbol, or a
    company name fragment) to the Instrument it identifies. Plain
    case-insensitive substring matching, not NLP/NER — deliberately: a
    keyword match a person can audit ("this article was tagged because it
    contains 'ICICIBANK'") is more trustworthy for a trading tool than an
    opaque model call that might mis-tag silently, and it's honest about
    what it is rather than dressed up as more sophisticated than it is."""
    text_upper = text.upper()
    matched = []
    seen_ids = set()
    for keyword, instrument in instrument_lookup.items():
        if not keyword:
            continue
        # Word-boundary match so "ITC" doesn't match inside "ITCHY" — not
        # that that's a real ticker, but the principle holds generally.
        if re.search(rf"\b{re.escape(keyword.upper())}\b", text_upper):
            instrument_id = getattr(instrument, "id", instrument)
            if instrument_id not in seen_ids:
                matched.append(instrument)
                seen_ids.add(instrument_id)
    return matched
