import matplotlib as mpl
mpl.use('Agg')  # headless mode
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from scipy.interpolate import CubicSpline
from datetime import datetime
import numpy as np
import urllib.request
import io
from PIL import Image


class PlotBuilder:
    def __init__(self, weather_dict):
        self.weather_dict = weather_dict
        pass

    @staticmethod
    def smooth_curve(x, y):
        """
        Return smooth curve using cubic spline interpolation
        :param x:
        :param y:
        :return: x_range, y_interp
        """
        # Perform clamped cubic spline interpolation on the temperature data
        cs = CubicSpline(x, y, bc_type='natural')

        # Generate a range of time values for plotting the curve
        x_range = np.linspace(x[0], x[-1], 100)

        # Evaluate the interpolated curve for the range of time values
        y_interp = cs(x_range)

        # Set the first and last points of the interpolated curve to the original data points
        y_interp[0] = y[0]
        y_interp[-1] = y[-1]
        return x_range, y_interp

    @staticmethod
    def get_image_by_icon_id(icon_id):
        """
        Return image from openweathermap.org for correspondent icon_id
        :param icon_id: str, e.g. '02n'
        :return: (np.array), image of the icon
        """
        img_url = 'https://openweathermap.org/img/wn/{}@2x.png'.format(icon_id)
        with urllib.request.urlopen(img_url) as url:
            img_data = url.read()
        img = np.array(Image.open(io.BytesIO(img_data)))
        return img

    def plot_weather_ts(self, show=False):
        # Get smooth curves
        time_ts_smooth, temp_ts_smooth = self.smooth_curve(self.weather_dict['time_ts'], self.weather_dict['temp_ts'])
        time_ts_smooth, temp_feels_like_ts_smooth = self.smooth_curve(self.weather_dict['time_ts'],
                                                                      self.weather_dict['temp_feels_like_ts'])

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(time_ts_smooth, temp_ts_smooth, label='Real', marker=None)
        ax.plot(time_ts_smooth, temp_feels_like_ts_smooth, label='Feels like', marker=None)
        ax.set_xlabel('Time, h')
        ax.set_ylabel('Temperature, °C')
        ax.legend(loc='upper right', fancybox=True, framealpha=0.5)
        title_date = datetime.fromtimestamp(self.weather_dict['time_sunrise']).strftime("%d %B %Y")
        title = f"{self.weather_dict['city']}, {self.weather_dict['country']}, {title_date}"
        ax.set_title(title)

        # Label the x_axis
        hour_label_lst = [datetime.fromtimestamp(timestamp).strftime('%H:00') for timestamp in
                          self.weather_dict['time_ts']]
        ax.set_xticks(self.weather_dict['time_ts'])
        ax.set_xticklabels(hour_label_lst)

        # Fill the area between sunset and sunrise with a dark color
        time_ts = np.array(self.weather_dict['time_ts'])
        night_mask = (time_ts >= self.weather_dict['time_sunset']) | (time_ts <= self.weather_dict['time_sunrise'])
        ax.fill_between(time_ts, min(self.weather_dict['temp_ts']), max(self.weather_dict['temp_ts']), where=night_mask,
                        facecolor='black', alpha=0.3)

        # Plot icons
        icon_img_lst = [self.get_image_by_icon_id(icon_id) for icon_id in self.weather_dict['icon_ts']]
        y_center_coord = (ax.get_ylim()[0] + ax.get_ylim()[1]) / 2
        for x_coord, icon_img in zip(self.weather_dict['time_ts'], icon_img_lst):
            ab = AnnotationBbox(OffsetImage(icon_img, zoom=0.25), (x_coord, y_center_coord), frameon=False)
            ax.add_artist(ab)

        if not show:
            plt.close(fig)
        # Save the plot
        plot_path = 'weather.png'
        fig.savefig(plot_path, bbox_inches='tight')
        return plot_path
