import os
import pandas as pd
import numpy as np
from time import time

# Dash
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import plotly.graph_objs as go
import dash_daq as daq

# Pymeasure
from pymeasure.adapters import PrologixAdapter
from pymeasure.instruments.keithley import Keithley2400


################################
# Semaphore and Global Variables
################################

class Semaphore:
    '''
    A single instrument can be operated at one time so a single instance of the app should be allowed on an individual machine.
    '''
    def __init__(self, filename='semaphore.txt'):
        self.filename = filename
        with open(self.filename, 'w') as f:
            f.write('done')

    def lock(self):
        with open(self.filename, 'w') as f:
            f.write('working')

    def unlock(self):
        with open(self.filename, 'w') as f:
            f.write('done')

    def is_locked(self):
        return open(self.filename, 'r').read() == 'working'


class GlobalVariables(object):
    '''
    Class used to store global variables. 
    Note: a single instance of the app is allowed per machine
    '''
    def __init__(self):
        self.scm = None # Stores the sourcemeter instrument when connected.



#########################
# Dashboard Layout / View
#########################

# Create the Dash app and get bootstrap CSS
app = dash.Dash()
app.css.append_css({
    "external_url": "https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css"
})

# Default empty Figure
fig_empty_default = go.Figure(data = [], layout = go.Layout(
    xaxis=dict(title='Time (s)',range=[0, 20], gridwidth=1),
    yaxis=dict(title='Current (mA)', range=[0, 20]),
    ))

# Initialize global variables
glbVar = GlobalVariables()

# Main layout
app.layout = html.Div([

    # Title Row
    html.Div(
        [
            html.H1(
                'Keithley Controller',
                style = {'font-family': 'Helvetica',
                       "margin-top": "25",
                       "margin-bottom": "0",
                       "padding-left": 30},
                className = 'col-9',
            ),
            html.P(
                'An interactive controller for current response using a Keithley sourcemeter.',
                style = 
                    {
                        'font-family': 'Helvetica',
                        "font-size": "120%",
                        "width": "80%",
                        'padding-left': 30,
                    },
                className='col-9',
            )
        ],
        className = 'row'
    ),

    # Selectors
    html.Div(
        [
            # Live-Saved Toggle switch
            html.Div([
                daq.ToggleSwitch(
                    id='toggle_live_saved',
                    label=["Live","Saved"],
                    style={'width': '100px', "padding-left": 30},
                    value=False,
                )
            ], className="col-2"),
            
            # Dropdown to select saved data to display
            html.Div([
                dcc.Dropdown(
                    id='dropdown_saved_files',
                    multi = True,
                    disabled = False,
                )
            ], className = "col-5"),
        ],
        className = 'row'
    ),

    # Graph + Setup
    html.Div([

        # Plot
        html.Div([
            dcc.Graph(
                id = "plot_current",
                style = {'margin-top': '20'},
                figure = fig_empty_default,
                animate = True
            )
        ], className = "col-9"),

        # Mode and parameter
        html.Div([
            # Mode selector
            html.Div([
                html.H2(
                    'Mode',
                    style = {'font-family': 'Helvetica'},
                ),
                daq.ToggleSwitch(
                    id='toggle_voltage_current',
                    label=['Voltage', 'Current'],
                    style={'width': '200px'},
                    value = False,
                ),
                html.H2(
                    'Parameters',
                    style = {'font-family': 'Helvetica', 'margin-top' : '20'},
                ),
                html.Label('Experiment Name', style = {'margin-top' : '20'}),
                html.Br(),
                dcc.Input(
                    id = 'input_exp_name',
                    type = 'text',
                ),
                html.Br()
            ]),

            # Parameter Selection - Voltage Mode
            html.Div([
                html.Label('Voltage (V)', style = {'margin-top' : '20'}),
                html.Br(),
                dcc.Input(
                    id = 'input_voltage_value',
                    type = 'number',
                    value = 0,
                    step = 0.1,
                    style = {'float': 'left'},
                ),
                html.Br(),
                html.Br(),
                html.Label('Max current (mA)', style = {'margin-top' : '20'}),
                html.Br(),
                dcc.Input(
                    id = 'input_max_current',
                    type = 'number',
                    value = 0,
                    step = 5,
                    style = {'float': 'left'},
                ),
            ], style = {'display': 'block'}, id = "div_parameter_selection_voltage"),

            # Parameter Selection - Current Mode
            html.Div([
                html.Label('Current (mA)', style = {'margin-top' : '20'}),
                html.Br(),
                dcc.Input(
                    id = 'input_current_value',
                    type = 'number',
                    value = 0,
                    step = 0.1,
                    style = {'float': 'left'},
                ),
                html.Br(),
                html.Br(),
                html.Label('Max voltage (V)', style = {'margin-top' : '20'}),
                html.Br(),
                dcc.Input(
                    id = 'input_max_voltage',
                    type = 'number',
                    value = 0,
                    step = 0.1,
                    style = {'float': 'left'},
                ),
            ], style = {'display': 'none'}, id = "div_parameter_selection_current"),

            # Toggle autostop
            html.Br(),
            html.Br(),
            html.Label('Autostop'),
            html.Br(),
            daq.ToggleSwitch(
                id = "toggle_autostop",
                label = ["Off", "On"],
                style = {'width': '100px'},
                value = 'Off',
            ),

            # Run experiment
            html.Button(
                'Run',
                id = "button-run-experiment",
                style = {'margin': 'auto', 'margin-top': '25'},
                className = "btn btn-primary"
            )

        ], className = "col-3")
    ], className = "row"),

    # Instrument connection
    html.Div([

        # Connect button
        html.Div([
            daq.PowerButton(
                id = "button_instrument_connect",
                on = False,
                label = "Connect",
                labelPosition = "bottom",
                disabled=True,
                style = {"padding-left": 30}
            )
        ], className = "col-1"),

        # Port name
        html.Div([
            html.Label('Port: '),
            dcc.Input(
                id = 'input_port_name',
                type = 'text',
                style = {'margin-left': '20'}
            ),
        ], className = "col-4"),

        # Status
        html.Div([
            html.Label('Status: '),
            html.Label(
                children = ['Not connected'],
                id = 'label_status',
                style = {'margin-left': '20'}
            )
        ], className = "col-3"),

    ], className = 'row'),

    # # Live measurements
    # html.Div([

    #     # Voltage
    #     html.Div([
    #         html.Label(
    #             'Voltage (V):',
    #             ),
    #         html.Br(),
    #         daq.LEDDisplay(
    #             id = "led_voltage",
    #             value = 0.0
    #         )
    #     ], className = 'col-3'),

    #     # Current
    #     html.Div([
    #         html.Label(
    #             'Current (mA):',
    #             ),
    #         html.Br(),
    #         daq.LEDDisplay(
    #             id = "led_current",
    #             value = 000
    #         )
    #     ], className = 'col-3')

    # ], className = 'row justify-content-around'),

    dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )

], className = '.container')


#############################################
# Interaction Between Components / Controller
#############################################

##### Live/Saved Switch and Dropdown #####

# Populate the saved file dropdown
@app.callback(
    Output('dropdown_saved_files', 'options'),
    [
        Input('toggle_live_saved', 'value'),
    ]
)
def populate_dropdown(live_saved):

    list_data = [file for file in os.listdir('data') if file.endswith('.pkl')]
    return [{'label': file.split('.')[0], 'value': file} for file in list_data]

#  Disable dropdown when live data is selected
@app.callback(
    Output('dropdown_saved_files', 'disabled'),
    [
        Input('toggle_live_saved', 'value')
    ]
)
def disable(live_saved):
    if live_saved: # Saved
        return False
    elif not live_saved: # Live
        return True

# Empty the dropdown when live data is selected
@app.callback(
    Output('dropdown_saved_files', 'value'),
    [
        Input('toggle_live_saved', 'value')
    ]
)
def disable(live_saved):
    if live_saved: # Saved
        pass
    elif not live_saved: # Live
        return None

##### Graph Update #####

# Update the graph
@app.callback(
    Output('plot_current', 'figure'),
    [
        Input('toggle_live_saved', 'value'),
        Input('dropdown_saved_files', 'value')
    ]
)
def display_plot(live_saved, file_names = None):
    if live_saved: # Saved
        # Generate graph from saved data
        return gen_plot_saved(file_names)
    else: # Live
        # Return the default figure
        return fig_empty_default


##### Mode selection #####

# Display / Hide Voltage parameters
@app.callback(
    Output('div_parameter_selection_voltage', 'style'),
    [
        Input('toggle_voltage_current', 'value')
    ]
)
def display_voltage_parameter(toggle_value):

    if toggle_value: # Current mode
        return {'display': 'none'}
    else: # Voltage mode
        return {'display': 'block'}

# Display / Hide Current parameters
@app.callback(
    Output('div_parameter_selection_current', 'style'),
    [
        Input('toggle_voltage_current', 'value')
    ]
)
def display_voltage_parameter(toggle_value):

    if toggle_value: # Current mode
        return {'display': 'block'}
    else: # Voltage mode
        return {'display': 'none'}


##### Instrument connection #####

# Try to connect to the instrument when the power button is pressed
@app.callback(
    Output('label_status', 'children'),
    [
        Input('button_instrument_connect', 'on')
    ],
    [
        State('input_port_name', 'value')
    ]
)
def connect_to_instrument(button_on, port):
    if button_on:
        try:
            instrument = Sourcemeter(port, 24)
            message = "Connected !"
        except Exception as ex:
            instrument = None
            message = "Connection Failed -- {}".format(type(ex).__name__)
        glbVar.scm = instrument
        return message
    else:
        # Reinitialize scm
        if isinstance(glbVar.scm, Sourcemeter):
            glbVar.scm = None
        return "Not connected"

# Disable the power button unless the port name is valid
@app.callback(
    Output('button_instrument_connect', 'disabled'),
    [
        Input('input_port_name', 'value')
    ],
)
def instrument_port_btn_update(text):
    """enable or disable the connect button
    depending on the port name
    """

    answer = True

    if isinstance(text, str):
        if text.startswith('/dev/tty.'):
            answer = False

    return answer

#############################################
# Model / Data Retrieval
#############################################

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


        


# start Flask server
if __name__ == '__main__':

    semaphore = Semaphore()

    if not semaphore.is_locked():
        semaphore.lock()
        try:
            app.run_server(
                debug=True,
                host='0.0.0.0',
                port=8050
        )
        except Exception as ex:
            print(ex)
        finally:
            semaphore.unlock()
    else:
        print("An instance of this app is already running on this machine.")
