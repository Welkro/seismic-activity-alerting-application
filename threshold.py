import lightningchart as lc
import time
from obspy.core import Stream
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.signal.filter import lowpass

lc.set_license("LICENSE_KEY")

chart = lc.ChartXY(title='Seismic Data Threshold Warning',
                   theme=lc.Themes.Dark).open(live=True)

# Dispose the default x axis and create a high precision x axis
chart.get_default_x_axis().dispose()
x_axis = chart.add_x_axis(axis_type='linear-highPrecision')
x_axis.set_tick_strategy('DateTime')
x_axis.set_scroll_strategy('progressive')
x_axis.set_interval(start=0, end=10000, stop_axis_after=False)

series = chart.add_line_series(
    data_pattern='ProgressiveX').set_line_thickness(2)

y_axis = chart.get_default_y_axis()
y_axis.set_title("Amplitude")

constant_line = y_axis.add_constant_line().set_interaction_move_by_dragging(False)
constant_line.set_value(350)
constant_line.set_stroke(2.5, lc.Color(255, 0, 0))

constant_line2 = y_axis.add_constant_line().set_interaction_move_by_dragging(False)
constant_line2.set_value(-350)
constant_line2.set_stroke(2.5, lc.Color(255, 0, 0))

series.set_line_color_lookup_table(
    steps=[
        {'value': 350, 'color': lc.Color('red')},
        {'value': 175, 'color': lc.Color('yellow')},
        {'value': -175, 'color': lc.Color('green')},
        {'value': -350, 'color': lc.Color('yellow')},
        {'value': -400, 'color': lc.Color('red')},
    ],
    look_up_property='y',
    interpolate=True,
    percentage_values=False
)

chart.get_default_y_axis().set_color_lookup_table(
    steps=[
        {'value': 350, 'color': lc.Color('red')},
        {'value': 175, 'color': lc.Color('yellow')},
        {'value': -175, 'color': lc.Color('green')},
        {'value': -350, 'color': lc.Color('yellow')},
        {'value': -400, 'color': lc.Color('red')},
    ],
    look_up_property='y',
    interpolate=False,
    percentage_values=False
)


class MyClient(EasySeedLinkClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.series = series
        self.data = []
        self.stream = Stream()

    def append_to_chart(self):
        if self.data:
            x, y = self.data.pop(0)
            self.series.add(x, y)
            time.sleep(0.01)

    def on_data(self, trace):
        print('Received trace:')
        print(trace)

        # Calculate the Nyquist frequency and set the lowpass filter cut-off
        nyquist_freq = trace.stats.sampling_rate / 2
        cutoff_freq = nyquist_freq * 0.4  # Setting cut-off at 40% of Nyquist frequency

        # Apply lowpass filter with the calculated cut-off frequency
        trace.filter('lowpass', freq=cutoff_freq, corners=4, zerophase=True)

        self.stream += trace

        x_values_seconds = trace.times().tolist()
        start_time = trace.stats.starttime.timestamp * 1000
        x_values = [start_time + sec * 1000 for sec in x_values_seconds]
        y_values = trace.data.tolist()

        for x, y in zip(x_values, y_values):
            self.data.append((x, y))
            self.append_to_chart()


client = MyClient('rtserve.iris.washington.edu:18000')
client.select_stream('WI', 'BIM', 'HHZ')
client.run()