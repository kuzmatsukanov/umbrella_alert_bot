import requests


class OpenweathermapParser:
    def __init__(self, city, api_key):
        """
        Get data with a 3-day weather forecast with 3h time resolution
        :param city: str, e.g. 'Tel Aviv'
        :param api_key: str, api_key for api.openweathermap.org
        """
        url = 'http://api.openweathermap.org/data/2.5/forecast?q={}&appid={}&units=metric'.format(city, api_key)
        response = requests.get(url)
        self.weather_forecast = response.json()

    def get_weather_dict(self):
        """
        Extracts relevant weather data from the current weather forecast
        :return: dict, dcitionary containing weather data for the first 7 time steps (3 hours each).
        """
        weather_ts = self.weather_forecast['list'][0:7]
        weather_dict = {
            'temp_ts': [],
            'temp_feels_like_ts': [],
            'time_ts': [],
            'icon_ts': [],
            'main': [],
            'description': [],
            'time_sunrise': self.weather_forecast['city']['sunrise'],
            'time_sunset': self.weather_forecast['city']['sunset'],
            'city': self.weather_forecast['city']['name']
        }
        for weather in weather_ts:
            weather_dict['temp_ts'].append(weather['main']['temp'])
            weather_dict['temp_feels_like_ts'].append(weather['main']['feels_like'])
            weather_dict['time_ts'].append(weather['dt'])
            weather_dict['icon_ts'].append(weather['weather'][0]['icon'])
            weather_dict['main'].append(weather['weather'][0]['main'])
            weather_dict['description'].append(weather['weather'][0]['description'])
        return weather_dict
