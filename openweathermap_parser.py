import requests
from logger import logger


class OpenweathermapParser:
    def __init__(self, api_key):
        """
        Class request and parse openweathermap.org data with a 3-day weather forecast with 3h time resolution
        :param api_key: str, api_key for api.openweathermap.org
        """
        self._api_key = api_key

    def _make_url_get_weather_by_city(self, city):
        """
        Make URL for API request to openweathermap.org data for given city
        :param city: (str) name of city
        :return: (str) url
        """
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self._api_key}&units=metric"
        return url

    def _make_url_get_weather_by_latlon(self, lat, lon):
        """
        Make URL for API request to openweathermap.org data for given latitude and longitude
        :return: (str) url
        """
        url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self._api_key}&units=metric"
        return url

    def request_openweathermap_by_city(self, city):
        """Make API request to openweathermap.org data for given city"""
        url = self._make_url_get_weather_by_city(city)
        response = requests.get(url)
        return response

    def request_openweathermap_by_latlon(self, lat, lon):
        """Make API request to openweathermap.org data for given latitude and longitude"""
        url = self._make_url_get_weather_by_latlon(lat, lon)
        response = requests.get(url)
        return response

    @staticmethod
    def parse_response_metadata(response):
        """
        Parse response from api request to openweathermap.org
        :param response: (requests.models.Response) response from api.openweathermap.org
        :return: (dict), {'cod': cod, 'lat': lat, 'lon': lon, 'city': city, 'country': country} or
         {'cod': cod} meaning the request is not correct
        """
        response_dict = response.json()
        cod = response_dict['cod']
        if cod in ("401", "404"):
            logger.error(response_dict['message'])
            metadata_dict = {'cod': cod}
            return metadata_dict
        lat = response_dict['city']['coord']['lat']
        lon = response_dict['city']['coord']['lon']
        city = response_dict['city']['name'] if response_dict['city']['name'] != '' else 'unknown'
        country = response_dict['city']['country'] if response_dict['city']['country'] != '' else 'unknown'
        metadata_dict = {'cod': cod, 'lat': lat, 'lon': lon, 'city': city, 'country': country}
        return metadata_dict

    def get_weather_dict(self, lat, lon, max_attempts=10):
        """
        Extracts relevant weather data from the current weather forecast
        :lat: (float) latitude
        :lon: (float) longitude
        :max_attempts: int, maximum number of attempts to make the request (default=10)
        :return: dict, dictionary containing weather data for the first 7 time steps (3 hours each) or None.
        """
        # Request OpenWeatherMap API
        for attempt in range(1, max_attempts):
            response = self.request_openweathermap_by_latlon(lat, lon)
            weather_data = response.json()

            # Check response code
            if weather_data['cod'] == "401":
                logger.error(weather_data['message'])
                return None
            elif weather_data['cod'] == "404":
                logger.error(f"Failed to request: {lat}, {lon}")
                return None
            elif weather_data['cod'] == "200":
                logger.info(f"Successfully fetched weather forecast on attempt {attempt}")
                weather_dict = self.parse_weather_data(weather_data)
                return weather_dict
            else:
                logger.warning(f"Attempt {attempt}: Failed to fetch weather forecast. Response text: {response.text}")
                return None

    @staticmethod
    def parse_weather_data(weather_data):
        """
        Parse weather data
        :param weather_data: dictionary of the success response from api.openweather.org
        :return: dict, dictionary containing weather data for the first 7 time steps (3 hours each)
        """
        weather_ts = weather_data['list'][0:7]
        weather_dict = {
            'temp_ts': [],
            'temp_feels_like_ts': [],
            'time_ts': [],
            'icon_ts': [],
            'main': [],
            'description': [],
            'time_sunrise': weather_data['city']['sunrise'],
            'time_sunset': weather_data['city']['sunset'],
            'city': weather_data['city']['name'],
            'country': weather_data['city']['country']
        }
        for weather in weather_ts:
            weather_dict['temp_ts'].append(weather['main']['temp'])
            weather_dict['temp_feels_like_ts'].append(weather['main']['feels_like'])
            weather_dict['time_ts'].append(weather['dt'])
            weather_dict['icon_ts'].append(weather['weather'][0]['icon'])
            weather_dict['main'].append(weather['weather'][0]['main'])
            weather_dict['description'].append(weather['weather'][0]['description'])
        return weather_dict
