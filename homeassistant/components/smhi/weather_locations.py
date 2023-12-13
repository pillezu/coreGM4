"""Weather Locations."""

import json
from typing import Any

from .const import weather_conditions, weather_icons
from .downloader import SmhiDownloader
from .smhi_geolocation_event import SmhiGeolocationEvent


class SmhiWeatherLocations:
    """Class for SMHI Weather Locations.

    This class creates geolocation events for a set of notable cities. These events contain weather data for each of the city locations.
    """

    celsius_symbol = chr(176) + "C"
    temperature_par_name = "t"
    weather_condition_par_name = "Wsymb2"

    def get_cities(self) -> list:
        """Get the cities which will be used as weather locations."""
        # Open the JSON file for reading
        with open(
            "homeassistant/components/smhi/notable_cities.json", encoding="utf-8"
        ) as file:
            # Load the JSON data from the file
            data = json.load(file)

        # Parse each city entry
        cities = []
        for city in data["cities"]:
            parsed_city = {
                "name": city.get("city"),
                "latitude": float(city.get("lat")),
                "longitude": float(city.get("lng")),
            }
            cities.append(parsed_city)

        return cities

    async def get_weather_data(self, lat: float, lon: float) -> Any:
        """Get weather data from SMHI api based on specific latitude and longitude coordinates.

        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
        """
        weather_api_url = f"https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{lon}/lat/{lat}/data.json"

        # Fetch weather data from the API
        smhi_downloader = SmhiDownloader()
        data = await smhi_downloader.download_json(weather_api_url)

        return data

    async def get_weather_locations(self) -> list[SmhiGeolocationEvent]:
        """Create and return weather location entities for each notable city."""
        weather_location_entities = []

        # For each notable city, fetch weather data for that location and create a geoloation event
        for city in self.get_cities():
            city_weather_data = await self.get_weather_data(
                city["latitude"], city["longitude"]
            )
            timeseries_data = city_weather_data.get("timeSeries")[0]

            # TEMPERATURE - get temperature value and parse it
            temperature = self.get_parameter_value(
                timeseries_data, self.temperature_par_name
            )
            temperature_text = str(temperature) + " " + self.celsius_symbol

            # WEATHER CONDITION - get the weather condition index, and then its icon and description
            weather_condition_index = self.get_parameter_value(
                timeseries_data, self.weather_condition_par_name
            )
            condition_icon = self.get_weather_condition_icon(weather_condition_index)
            icon_url = weather_icons[condition_icon]
            condition_name = weather_conditions[str(weather_condition_index)]

            # Create geolocation event based on the data
            geolocation_event = SmhiGeolocationEvent(
                city["name"]
                + " - Temperature: "
                + temperature_text
                + ", "
                + condition_name,
                city["latitude"],
                city["longitude"],
                icon_url,
                "mdi:cloud-outline",
                "stationary",
                "weather",
            )
            weather_location_entities.append(geolocation_event)

        return weather_location_entities

    def get_parameter_value(self, timeseries_data: Any, parameter_name: str) -> int:
        """Get the value from a parameter in the 'timeSeries' data.

        Args:
            timeseries_data: The timeseries data from the api
            parameter_name: Name of the parameter to fetch the value from
        """

        # Get all parameters and loop through each of them to find correct parameter. Return its value
        parameters = timeseries_data.get("parameters")
        for data in parameters:
            if data["name"] == parameter_name:
                return int(data["values"][0])

        # If specified parameter could not be found
        raise ValueError("Value not found in the data.")

    def get_weather_condition_icon(self, weather_condition_index: int) -> str:
        """Get the weather condition icon.

        Args:
            weather_condition_index: Index for the weather condition.
        """
        # Index | Meaning
        # 1	      Clear sky
        # 2	      Nearly clear sky
        # 3	      Variable cloudiness
        # 4	      Halfclear sky
        # 5	      Cloudy sky
        # 6	      Overcast
        # 7	      Fog
        # 8	      Light rain showers
        # 9	      Moderate rain showers
        # 10	  Heavy rain showers
        # 11	  Thunderstorm
        # 12	  Light sleet showers
        # 13	  Moderate sleet showers
        # 14	  Heavy sleet showers
        # 15	  Light snow showers
        # 16	  Moderate snow showers
        # 17	  Heavy snow showers
        # 18	  Light rain
        # 19	  Moderate rain
        # 20	  Heavy rain
        # 21	  Thunder
        # 22	  Light sleet
        # 23	  Moderate sleet
        # 24	  Heavy sleet
        # 25	  Light snowfall
        # 26	  Moderate snowfall
        # 27	  Heavy snowfall

        # Clear sky
        if weather_condition_index in (1, 2, 3):
            return "SUN"
        # Clouds
        if weather_condition_index in (4, 5, 6, 7):
            return "CLOUD"
        # Rain
        if weather_condition_index in (8, 9, 10, 11, 18, 19, 20, 21):
            return "RAIN"
        # Snow
        if weather_condition_index in (
            12,
            13,
            14,
            15,
            16,
            17,
            22,
            23,
            24,
            25,
            26,
            27,
        ):
            return "SNOWFLAKE"

        # The given index is not a known weather condition
        return "NULL"
