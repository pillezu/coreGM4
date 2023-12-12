"""warnings."""
from typing import Any

from .const import smhi_warning_icons
from .downloader import SmhiDownloader
from .smhi_geolocation_event import SmhiGeolocationEvent


class SmhiWarnings:
    """SmhiWarning."""

    async def get_warnings(self) -> list[SmhiGeolocationEvent]:
        """Get warning data from smhi api."""
        warnings_url = (
            "https://opendata-download-warnings.smhi.se/ibww/api/version/1/warning.json"
        )
        smhi_downloader = SmhiDownloader()
        data = await smhi_downloader.download_json(warnings_url)

        if isinstance(data, list):
            return self.parse_warnings(data)
        return []

    def parse_warnings(self, data: list[dict[str, Any]]) -> list[SmhiGeolocationEvent]:
        """Parse warning data from smhi api."""
        geo_location_entities = []

        for warning in data:
            parsed_warning = self.parse_individual_warning(warning)
            geo_location_entities.extend(
                self.create_geo_entities_from_warning(parsed_warning)
            )

        return geo_location_entities

    def parse_individual_warning(self, warning: dict[str, Any]) -> dict:
        """Parse individual warning and its areas."""
        parsed_warning = {
            "id": warning.get("id"),
            "normalProbability": warning.get("normalProbability"),
            "event": warning.get("event", {}),
            "descriptions": warning.get("descriptions", []),
            "warningAreas": [
                self.parse_warning_area(area)
                for area in warning.get("warningAreas", [])
            ],
        }

        return parsed_warning

    def parse_warning_area(self, area: dict[str, Any]) -> dict:
        """Parse individual warning area."""

        return {
            "id": area.get("id"),
            "approximateStart": area.get("approximateStart"),
            "published": area.get("published"),
            "normalProbability": area.get("normalProbability"),
            "areaName": area.get("areaName", {}),
            "warningLevel": area.get("warningLevel", {}),
            "eventDescription": area.get("eventDescription", {}),
            "affectedAreas": area.get("affectedAreas", []),
            "descriptions": area.get("descriptions", []),
            "geometry": area.get("area", {}).get("geometry", {}),
        }

    def create_geo_entities_from_warning(
        self, warning: dict
    ) -> list[SmhiGeolocationEvent]:
        """Create geo location entities from a parsed warning."""

        entities = []

        for area in warning["warningAreas"]:
            name = str(area["descriptions"][0]["text"]["en"])
            icon = str(area["warningLevel"]["code"])
            icon_url = smhi_warning_icons.get(icon, "")

            coordinates = area["geometry"].get("coordinates", [])
            if len(coordinates) == 1:
                coordinates = coordinates[0]

            for x in range(0, len(coordinates), 60):
                entities.append(
                    SmhiGeolocationEvent(
                        name,
                        coordinates[x][1],
                        coordinates[x][0],
                        icon_url,
                        "mdi:alert",
                        "stationary",
                        "warnings",
                    )
                )

        return entities
