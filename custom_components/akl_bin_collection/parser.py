"""Parse Auckland Council collection pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from typing import Final


class CollectionPageError(Exception):
    """Raised when collection details cannot be found in a council page."""


@dataclass(frozen=True, slots=True)
class ParsedCollectionPage:
    """Collection details extracted from a council page."""

    address: str | None
    dates: dict[str, date | None]


_ICON_TYPES: Final = {
    "rubbish": "rubbish",
    "recycle": "recycling",
    "food-waste": "food_scraps",
}

_MONTHS: Final = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_DATE_PATTERN: Final = re.compile(
    r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
    r",?\s+(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)$",
    re.IGNORECASE,
)

_VOID_ELEMENTS: Final = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def _normalized_text(parts: list[str]) -> str:
    """Join text nodes while preserving boundaries between nested elements."""
    return " ".join(" ".join(parts).split())


def parse_collection_date(value: str, today: date) -> date:
    """Convert a council date without a year to the next matching date."""
    normalized = " ".join(value.split())
    match = _DATE_PATTERN.fullmatch(normalized)
    if match is None:
        raise CollectionPageError(f"Unsupported collection date: {value!r}")

    month_name = match.group("month").casefold()
    month = _MONTHS.get(month_name)
    if month is None:
        raise CollectionPageError(f"Unsupported collection month: {month_name!r}")

    day = int(match.group("day"))
    try:
        result = date(today.year, month, day)
        if result < today:
            result = date(today.year + 1, month, day)
    except ValueError as err:
        raise CollectionPageError(f"Invalid collection date: {value!r}") from err
    return result


class _CollectionHTMLParser(HTMLParser):
    """Small purpose-built parser for the council schedule card."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[str] = []
        self._active_h2_depth: int | None = None
        self._h2_parts: list[str] = []
        self._last_h2: str | None = None

        self._card_depth: int | None = None
        self._card_title_depth: int | None = None
        self._card_title_parts: list[str] = []
        self._card_items: list[tuple[str, str]] = []

        self._item_depth: int | None = None
        self._item_type: str | None = None
        self._date_depth: int | None = None
        self._date_parts: list[str] = []

        self.address: str | None = None
        self.items: list[tuple[str, str]] | None = None

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        return {
            css_class
            for key, value in attrs
            if key == "class" and value
            for css_class in value.split()
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        depth = len(self._stack) + 1
        if tag not in _VOID_ELEMENTS:
            self._stack.append(tag)
        classes = self._classes(attrs)

        if self.items is not None:
            return

        if self._card_depth is None:
            if tag == "h2":
                self._active_h2_depth = depth
                self._h2_parts = []
            if tag == "div" and "acpl-schedule-card" in classes:
                self._card_depth = depth
                self._card_title_parts = []
                self._card_items = []
            return

        if tag == "h4" and "card-title" in classes:
            self._card_title_depth = depth

        if (
            self._item_depth is None
            and tag == "span"
            and "acpl-icon-with-attribute" in classes
        ):
            self._item_depth = depth
            self._item_type = None
            self._date_parts = []
            return

        if self._item_depth is not None:
            if tag == "i":
                for icon_class, collection_type in _ICON_TYPES.items():
                    if icon_class in classes:
                        self._item_type = collection_type
                        break
            elif tag == "b":
                self._date_depth = depth

    def handle_data(self, data: str) -> None:
        if self._active_h2_depth is not None:
            self._h2_parts.append(data)
        if self._card_title_depth is not None:
            self._card_title_parts.append(data)
        if self._date_depth is not None:
            self._date_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        depth = len(self._stack)

        if tag == "h2" and self._active_h2_depth == depth:
            heading = _normalized_text(self._h2_parts)
            if heading:
                self._last_h2 = heading
            self._active_h2_depth = None
            self._h2_parts = []

        if tag == "b" and self._date_depth == depth:
            self._date_depth = None

        if tag == "span" and self._item_depth == depth:
            collection_date = _normalized_text(self._date_parts)
            if self._item_type is not None and collection_date:
                self._card_items.append((self._item_type, collection_date))
            self._item_depth = None
            self._item_type = None
            self._date_depth = None
            self._date_parts = []

        if tag == "h4" and self._card_title_depth == depth:
            self._card_title_depth = None

        if tag == "div" and self._card_depth == depth:
            title = _normalized_text(self._card_title_parts)
            if "household collection" in title.casefold() and self._card_items:
                self.address = self._last_h2
                self.items = self._card_items.copy()
            self._card_depth = None
            self._card_title_depth = None
            self._card_title_parts = []
            self._card_items = []

        if tag in self._stack:
            matching_index = len(self._stack) - 1 - self._stack[::-1].index(tag)
            del self._stack[matching_index:]


def parse_collection_page(html: str, today: date) -> ParsedCollectionPage:
    """Extract the next household collection dates from HTML."""
    parser = _CollectionHTMLParser()
    try:
        parser.feed(html)
        parser.close()
    except (UnicodeError, ValueError) as err:
        raise CollectionPageError("The collection page is not valid HTML") from err

    if parser.items is None:
        raise CollectionPageError(
            "No household collection data found; the property ID may be invalid "
            "or the council page may have changed"
        )

    dates: dict[str, date | None] = {
        "rubbish": None,
        "recycling": None,
        "food_scraps": None,
    }
    for collection_type, value in parser.items:
        if dates[collection_type] is None:
            dates[collection_type] = parse_collection_date(value, today)

    if not any(dates.values()):
        raise CollectionPageError("No collection dates found in the household card")

    return ParsedCollectionPage(address=parser.address, dates=dates)
