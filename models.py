import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Pymeasure
from pymeasure.adapters import PrologixAdapter
from pymeasure.instruments.keithley import Keithley2400


##### Sourcemeter ######

class Sourcemeter(object):

    def __init__(self, serial_port, gpib_address, serial_timeout = 0.1):
        
        # Grab kwarg variables
        self.port = serial_port
        self.address = gpib_address
        self.serial_timeout = serial_timeout

        # Initialize state variables as properties
        self._measurement_mode = None
        @property
        def measurement_mode(self):
            return self._measurement_mode

        self._source_enabled = False
        @property
        def source_enabled(self):
            return self._source_enabled

        # Initialize the instrument upon creation
        self.adapter = PrologixAdapter(self.port, address = self.address, serial_timeout = self.serial_timeout)
        self._instrument = Keithley2400(self.adapter)

        # Ensure the Prologix adapter timeout is set to 100ms
        self._instrument.write("++read_tmo_ms 100")

        # Make sure the connection is properly established
        if not self._instrument.id.stratswith("KEITHLEY"):
            raise IOError("Instrument connection failed")


    def is_connected(self):
        return self._instrument.id.startswith("KEITHLEY")

    def setup_current_measurement(self, voltage, current_compliance):
        self._instrument.reset()
        self._instrument.apply_voltage(20, 0.1)
        self._instrument.measure_current(nplc=0.1, current=current_compliance, auto_range=False)
        self._instrument.source_voltage = voltage
        self._instrument.sample_continuously()
        self._measurement_mode = 'current'

    def setup_voltage_measurement(self, current, voltage_compliance):
        self._instrument.reset()
        self._instrument.apply_current(0.1, 6)
        self._instrument.measure_voltage(nplc=0.1, voltage=voltage_compliance, auto_range=False)
        self._instrument.source_current = current
        self._instrument.sample_continuously()
        self._measurement_mode = 'voltage'

    def get_current(self):
        if self._measurement_mode == 'current' and self._source_enabled:
            return self._instrument.current
        else:
            raise Exception("Instrument must be in current measurement mode with the source ON before measuring the current.")

    def get_voltage(self):
        if self._measurement_mode == 'voltage' and self._source_enabled:
            return self._instrument.voltage
        else:
            raise Exception("Instrument must be in voltage measurement mode with the source ON before measuring the voltage.")

    def enable(self):
        self._instrument.enable_source()
        self._source_enabled = True

    def disable(self):
        self._instrument.disable_source()
        self._source_enabled = False


###### Plotting #######

# Default empty Figure
fig_empty_default = go.Figure(data = [], layout = go.Layout(
    xaxis=dict(title='Time (s)',range=[0, 20], gridwidth=1),
    yaxis=dict(title='Current (mA)', range=[0, 20]),
    ))

# Generate a plot
def gen_plot_saved(file_names):

    data_cur = []

    # When no files are selected, return to empty default
    if file_names is None:
        return fig_empty_default

    # Initialize variables for plot layout
    max_time = 20
    max_current = 20

    # Read all selected data files and add them to the figure
    for filename in file_names:

        df = pd.read_pickle('data/' + filename)

        # TODO: adapt this code to the new structure of the dataframe
        for volt in df.columns[1:]:
            data_cur.append(go.Scatter(
                x = df["Time"],
                y = df[volt],
                name = str(volt) + " V",
                legendgroup =  filename
            ))

            max_time = int(np.max([max_time, np.max(df["Time"])]))
            max_current = int(1.05 * np.max([max_current, np.max(df[volt])]))

        

    fig_cur = go.Figure(
    data_cur,
    layout = go.Layout(
        xaxis=dict(title='Time (s)',range=[0, max_time], gridwidth=1),
        yaxis=dict(title='Current (mA)', range=[0, max_current]),
        )
    )

    return fig_cur