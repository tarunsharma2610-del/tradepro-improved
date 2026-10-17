from datetime import datetime

from app.services.news_parsing import match_instruments, parse_rss

# Real content, captured via a live fetch of https://www.business-standard.com/rss/home_page_top_stories.rss
# during development (Aug 18, 2026) — trimmed to a few items, not synthesized.
REAL_SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="https://search.yahoo.com/mrss/" xmlns:atom="https://www.w3.org/2005/Atom">
  <channel>
    <title><![CDATA[Home Page]]></title>
    <link>https://www.business-standard.com</link>
    <description><![CDATA[Business News: Get latest news on share market, personal finance news, economy news, stock market updates, company news, election results, politics news, breaking news at Business Standard.]]></description>
    <lastBuildDate>Tue, 18 Aug 2026 15:46:06 +0530</lastBuildDate>
    <item>
      <title><![CDATA[ICICI Bank raises fresh $750 million as overseas borrowing accelerates]]></title>
      <link>https://www.business-standard.com/companies/news/icici-bank-raises-750-million-five-year-dollar-bonds-fcnr-swap-window-126081800627_1.html</link>
      <guid>https://www.business-standard.com/companies/news/icici-bank-raises-750-million-five-year-dollar-bonds-fcnr-swap-window-126081800627_1.html</guid>
      <pubDate>Tue, 18 Aug 2026 14:09:16 +0530</pubDate>
      <description><![CDATA[The latest issue takes the lender's dollar debt fundraising to $2.05 billion in about a month as Indian banks accelerate overseas borrowing ahead of the RBI swap window's early closure]]></description>
      <media:group>
        <media:description><![CDATA[The latest issue takes the lender's dollar debt fundraising to $2.05 billion]]></media:description>
      </media:group>
    </item>
    <item>
      <title><![CDATA[NSE seeking valuation of as much as ₹5.26 trillion in planned IPO]]></title>
      <link>https://www.business-standard.com/markets/ipo/nse-seeks-up-to-55-billion-valuation-126081800405_1.html</link>
      <guid>https://www.business-standard.com/markets/ipo/nse-seeks-up-to-55-billion-valuation-126081800405_1.html</guid>
      <pubDate>Tue, 18 Aug 2026 11:51:06 +0530</pubDate>
      <description><![CDATA[At a $55 bn valuation, NSE's sale of 6% stake on offer could raise about ₹315 billion]]></description>
    </item>
    <item>
      <title><![CDATA[Apple software hints at foldable iPhone, camera-equipped AirPods]]></title>
      <link>https://www.business-standard.com/technology/tech-news/apple-software-hints-126081800368_1.html</link>
      <guid>https://www.business-standard.com/technology/tech-news/apple-software-hints-126081800368_1.html</guid>
      <pubDate>Tue, 18 Aug 2026 11:33:18 +0530</pubDate>
      <description><![CDATA[References in Apple's latest macOS software point to several unreleased devices]]></description>
    </item>
  </channel>
</rss>
"""


class _FakeInstrument:
    def __init__(self, id_, trading_symbol):
        self.id = id_
        self.trading_symbol = trading_symbol


def test_parses_all_items_from_real_captured_rss():
    items = parse_rss(REAL_SAMPLE_RSS)
    assert len(items) == 3
    assert items[0].title == "ICICI Bank raises fresh $750 million as overseas borrowing accelerates"
    assert items[0].link.startswith("https://www.business-standard.com/companies/news/icici-bank")
    assert "dollar debt fundraising" in items[0].summary


def test_pubdate_parsed_from_real_rfc822_format():
    items = parse_rss(REAL_SAMPLE_RSS)
    assert items[0].published_at is not None
    assert items[0].published_at.year == 2026
    assert items[0].published_at.month == 8
    assert items[0].published_at.day == 18


def test_ignores_the_media_namespace_extension_without_erroring():
    # The real feed's <media:group> children shouldn't confuse the parser
    # or leak into title/summary — this is exactly what real feeds look like.
    items = parse_rss(REAL_SAMPLE_RSS)
    assert "media" not in items[0].title.lower()


def test_malformed_xml_returns_empty_list_not_an_exception():
    assert parse_rss("<rss><channel><item><title>unterminated") == []


def test_empty_feed_returns_empty_list():
    assert parse_rss('<?xml version="1.0"?><rss><channel></channel></rss>') == []


def test_item_missing_title_or_link_is_skipped():
    xml = """<rss><channel>
        <item><title>Has title, no link</title></item>
        <item><link>https://example.com/no-title</link></item>
        <item><title>Complete</title><link>https://example.com/ok</link></item>
    </channel></rss>"""
    items = parse_rss(xml)
    assert len(items) == 1
    assert items[0].title == "Complete"


def test_match_instruments_finds_icici_in_the_real_article():
    instruments = {"ICICIBANK": _FakeInstrument(1, "ICICIBANK"), "TCS": _FakeInstrument(2, "TCS")}
    items = parse_rss(REAL_SAMPLE_RSS)
    icici_article = items[0].title + " " + (items[0].summary or "")

    # The real headline says "ICICI Bank", not the exact ticker "ICICIBANK" —
    # confirms this is a real-world matching gap worth knowing about, not
    # a hypothetical one: keyword matching won't catch every phrasing.
    matched = match_instruments(icici_article, instruments)
    assert matched == []  # honest result: "ICICI Bank" != "ICICIBANK" as a substring


def test_match_instruments_matches_the_exact_ticker_when_present():
    instruments = {"ICICIBANK": _FakeInstrument(1, "ICICIBANK"), "TCS": _FakeInstrument(2, "TCS")}
    matched = match_instruments("ICICIBANK reports strong quarterly earnings", instruments)
    assert len(matched) == 1
    assert matched[0].trading_symbol == "ICICIBANK"


def test_match_instruments_respects_word_boundaries():
    instruments = {"ITC": _FakeInstrument(1, "ITC")}
    assert match_instruments("The ITCHY situation continued", instruments) == []
    assert match_instruments("ITC reported quarterly results", instruments) != []


def test_match_instruments_deduplicates_by_instrument_id():
    same_instrument = _FakeInstrument(1, "TCS")
    instruments = {"TCS": same_instrument, "Tata Consultancy": same_instrument}
    matched = match_instruments("TCS, part of Tata Consultancy group", instruments)
    assert len(matched) == 1
