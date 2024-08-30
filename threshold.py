import lightningchart as lc
import time
from obspy.core import Stream
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.signal.filter import lowpass

# Set the license key for LightningChart Python
lc.set_license("LICENSE_KEY")

# Create a chart with a specific title and theme, and open it live
chart = lc.ChartXY(title='Seismic Data Threshold Warning',
                   theme=lc.Themes.Dark).open(live=True)

# Dispose the default x axis and create a high precision x-axis
chart.get_default_x_axis().dispose()
x_axis = chart.add_x_axis(axis_type='linear-highPrecision')

# Set tick strategy and scroll strategy for the x-axis
x_axis.set_tick_strategy('DateTime')
x_axis.set_scroll_strategy('progressive')
x_axis.set_interval(start=0, end=10000, stop_axis_after=False)

# Add a line series to the chart for displaying the data
series = chart.add_line_series(
    data_pattern='ProgressiveX').set_line_thickness(2)

# Configure the y-axis
y_axis = chart.get_default_y_axis()
y_axis.set_title("Amplitude")

# Set constant lines
constant_line_upper = y_axis.add_constant_line().set_interaction_move_by_dragging(False)
constant_line_upper.set_value(600)
constant_line_upper.set_stroke(2.5, lc.Color(255, 0, 0))

constant_line_lower = y_axis.add_constant_line().set_interaction_move_by_dragging(False)
constant_line_lower.set_value(-600)
constant_line_lower.set_stroke(2.5, lc.Color(255, 0, 0))

constant_line_caution_upper = y_axis.add_constant_line().set_interaction_move_by_dragging(False)
constant_line_caution_upper.set_value(300)
constant_line_caution_upper.set_stroke(2.5, lc.Color(255, 255, 0))

constant_line_caution_lower = y_axis.add_constant_line().set_interaction_move_by_dragging(False)
constant_line_caution_lower.set_value(-300)
constant_line_caution_lower.set_stroke(2.5, lc.Color(255, 255, 0))

# Set the color lookup table for the line series based on y-values
series.set_line_color_lookup_table(
    steps=[
        {'value': 600, 'color': lc.Color('red')},
        {'value': 300, 'color': lc.Color('yellow')},
        {'value': 0, 'color': lc.Color('green')},
        {'value': -300, 'color': lc.Color('yellow')},
        {'value': -600, 'color': lc.Color('red')},
    ],
    look_up_property='y',
    interpolate=True,
    percentage_values=False
)

# Set the color lookup table for the y-axis based on y-values
chart.get_default_y_axis().set_color_lookup_table(
    steps=[
        {'value': 600, 'color': lc.Color('red')},
        {'value': 300, 'color': lc.Color('yellow')},
        {'value': 0, 'color': lc.Color('green')},
        {'value': -300, 'color': lc.Color('yellow')},
        {'value': -600, 'color': lc.Color('red')},
    ],
    look_up_property='y',
    interpolate=False,
    percentage_values=False
)

# Custom EasySeedLinkClient for receiving and processing seismic data
class MyClient(EasySeedLinkClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.series = series    # Reference to the chart series
        self.data = []  # List to hold the data
        self.stream = Stream()  # ObsPy stream to store trace data

    # Append data to the chart
    def append_to_chart(self):
        if self.data:
            x, y = self.data.pop(0)
            self.series.add(x, y)
            time.sleep(0.01)    # Sleep to control the data update rate

    # Callback method when data is received
    def on_data(self, trace):
        print('Received trace:')
        print(trace)

        # Calculate the Nyquist frequency and set the lowpass filter cut-off
        nyquist_freq = trace.stats.sampling_rate / 2
        cutoff_freq = nyquist_freq * 0.4  # Setting cut-off at 40% of Nyquist frequency

        # Apply lowpass filter with the calculated cut-off frequency
        trace.filter('lowpass', freq=cutoff_freq, corners=4, zerophase=True)

        # Add the filtered trace to the stream
        self.stream += trace

        # Convert trace times to milliseconds for x-values
        x_values_seconds = trace.times().tolist()
        start_time = trace.stats.starttime.timestamp * 1000
        x_values = [start_time + sec * 1000 for sec in x_values_seconds]
        y_values = trace.data.tolist()

        # Append the x- and y-values to the data list
        for x, y in zip(x_values, y_values):
            self.data.append((x, y))
            self.append_to_chart()  # Update the chart with new data

# Initialize the client with the Seedlink server address
client = MyClient('rtserve.iris.washington.edu:18000')
# Select the stream to receive data from
client.select_stream('WI', 'CBE', 'HHZ')
# Start the client to begin receiving data
client.run()