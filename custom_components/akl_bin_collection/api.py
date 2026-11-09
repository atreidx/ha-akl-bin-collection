"""Auckland Council collection page client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import COLLECTION_URL_TEMPLATE
from .parser import CollectionPageError, parse_collection_page

_AUCKLAND_TIME_ZONE = ZoneInfo("Pacific/Auckland")
_MAX_RESPONSE_SIZE = 10 * 1024 * 1024
_REQUEST_TIMEOUT = ClientTimeout(total=30)

# Identify the integration honestly. A spoofed Chrome User-Agent is rejected
# by the council site with HTTP 406, while a plain client identifier is served.
_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-NZ,en;q=0.9",
    "User-Agent": (
        "ha-akl-bin-collection/0.1.0 "
        "(+https://github.com/atreidx/ha-akl-bin-collection)"
    ),
}


class AucklandCouncilError(Exception):
    """Base error for Auckland Council collection requests."""


class AucklandCouncilConnectionError(AucklandCouncilError):
    """Raised when Auckland Council cannot be reached."""


class AucklandCouncilInvalidPropertyError(AucklandCouncilError):
    """Raised when a property ID has no household collection data."""


@dataclass(frozen=True, slots=True)
class CollectionSchedule:
    """The next collection dates for one property."""

    property_id: str
    address: str | None
    rubbish: date | None
    recycling: date | None
    food_scraps: date | None

    def date_for(self, collection_type: str) -> date | None:
        """Return a collection date by entity key."""
        return getattr(self, collection_type)


def normalize_property_id(value: str) -> str:
    """Validate and normalize an Auckland Council property ID."""
    property_id = str(value).strip()
    if not property_id.isascii() or not property_id.isdigit():
        raise AucklandCouncilInvalidPropertyError(
            "The property ID must contain digits only"
        )
    if not 5 <= len(property_id) <= 20:
        raise AucklandCouncilInvalidPropertyError(
            "The property ID must be between 5 and 20 digits"
        )
    return property_id


def collection_url(property_id: str) -> str:
    """Return the public collection page URL for a property."""
    return COLLECTION_URL_TEMPLATE.format(property_id)


class AucklandCouncilApi:
    """Fetch collection data directly from the Auckland Council website."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_schedule(self, property_id: str) -> CollectionSchedule:
        """Fetch and parse a property's next collection dates."""
        property_id = normalize_property_id(property_id)
        url = collection_url(property_id)

        try:
            async with self._session.get(
                url, headers=_REQUEST_HEADERS, timeout=_REQUEST_TIMEOUT
            ) as response:
                if response.status == 404:
                    raise AucklandCouncilInvalidPropertyError(
                        f"Property {property_id} was not found"
                    )
                if response.status >= 400:
                    raise AucklandCouncilConnectionError(
                        f"Auckland Council returned HTTP {response.status}"
                    )
                body = await response.content.read(_MAX_RESPONSE_SIZE + 1)
                if len(body) > _MAX_RESPONSE_SIZE:
                    raise AucklandCouncilConnectionError(
                        "Auckland Council response was unexpectedly large"
                    )
                encoding = response.charset or "utf-8"
        except AucklandCouncilError:
            raise
        except (ClientError, TimeoutError) as err:
            raise AucklandCouncilConnectionError(
                "Unable to reach Auckland Council"
            ) from err

        try:
            parsed = parse_collection_page(
                body.decode(encoding, errors="replace"),
                datetime.now(_AUCKLAND_TIME_ZONE).date(),
            )
        except CollectionPageError as err:
            raise AucklandCouncilInvalidPropertyError(str(err)) from err

        return CollectionSchedule(
            property_id=property_id,
            address=parsed.address,
            rubbish=parsed.dates["rubbish"],
            recycling=parsed.dates["recycling"],
            food_scraps=parsed.dates["food_scraps"],
        )
