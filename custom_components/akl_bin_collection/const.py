"""Constants for the Auckland Council Bin Collection integration."""

from typing import Final

DOMAIN: Final = "akl_bin_collection"
CONF_PROPERTY_ID: Final = "property_id"

COLLECTION_URL_TEMPLATE: Final = (
    "https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/"
    "rubbish-recycling-collections/rubbish-recycling-collection-days/{}.html"
)

COLLECTION_TYPES: Final = ("rubbish", "recycling", "food_scraps")
