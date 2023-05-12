import requests
import json
from logger import logger


class OpenweathermapParser:
    def __init__(self, city, api_key):
        """
        Get data with a 3-day weather forecast with 3h time resolution
        :param city: str, e.g. 'Tel Aviv'
        :param api_key: str, api_key for api.openweathermap.org
        """
        self.city = city
        self._api_key = api_key

    def _make_url_get_weather_by_city(self):
        """
        Make URL for API request to openweathermap.org data for given city
        :return: (str) url
        """
        url = 'http://api.openweathermap.org/data/2.5/forecast?q={}&appid={}&units=metric'.\
            format(self.city, self._api_key)
        return url

    def request_openweathermap_by_city(self):
        url = self._make_url_get_weather_by_city()
        response = requests.get(url)
        return response

    def _request_weather_data(self, max_attempts=10):
        """
        Requests weather data from the OpenWeatherMap API.
        :param max_attempts: int, maximum number of attempts to make the request (default=10)
        :return: dict, weather data or None
        """
        for attempt in range(1, max_attempts):
            # Request OpenWeatherMap API
            response = self.request_openweathermap_by_city()
            response_text_dict = json.loads(response.text)

            # Check and parse the response
            if response_text_dict['cod'] == "200":
                weather_forecast = response.json()
                logger.info(f"Successfully fetched weather forecast on attempt {attempt}")
                return weather_forecast
            elif response_text_dict['cod'] == "401":
                logger.error(response_text_dict['message'])
                return None
            elif response_text_dict['cod'] == "404":
                logger.error(f"Failed to request city: {self.city}")
                return None
            else:
                logger.warning(f"Attempt {attempt}: Failed to fetch weather forecast. Response text: {response.text}")
        return None

    def get_weather_dict(self):
        """
        Extracts relevant weather data from the current weather forecast
        :return: dict, dictionary containing weather data for the first 7 time steps (3 hours each) or None.
        """
        weather_data = self._request_weather_data()
        if weather_data is None:
            return None
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
