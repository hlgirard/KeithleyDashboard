import os
import pandas as pd
import numpy as np

# Dash
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import plotly.graph_objs as go
import dash_daq as daq

#########################
# Dashboard Layout / View
#########################

# Create the Dash app and get bootstrap CSS
app = dash.Dash()
app.css.append_css({
    "external_url": "https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css"
})

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
                style = {'margin-top': '20'}
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
                    id='toggle_constant_feedback',
                    label=['Constant', 'Feedback'],
                    style={'width': '200px'},
                    value = 'Constant',
                )
            ]),

            # Parameter Selection
            html.Div([
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
                html.Br(),
                html.Label('Voltage', style = {'margin-top' : '20'}),
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
                html.Label('Autostop'),
                html.Br(),
                daq.ToggleSwitch(
                    id = "toggle_autostop",
                    label = ["Off", "On"],
                    style = {'width': '100px'},
                    value = 'Off',
                )
            ], id = "div_parameter_selection"),

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
                'NOT CONNECTED',
                id = 'label_status',
                style = {'margin-left': '20'}
            )
        ], className = "col-3"),

    ], className = 'row'),

    # Live measurements
    html.Div([

        # Voltage
        html.Div([
            html.Label(
                'Voltage (V):',
                ),
            html.Br(),
            daq.LEDDisplay(
                id = "led_voltage",
                value = 0.0
            )
        ], className = 'col-3'),

        # Current
        html.Div([
            html.Label(
                'Current (mA):',
                ),
            html.Br(),
            daq.LEDDisplay(
                id = "led_current",
                value = 000
            )
        ], className = 'col-3')

    ], className = 'row justify-content-around'),

    dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )

], className = '.container')


#############################################
# Interaction Between Components / Controller
#############################################

# Populate the saved file dropdown
@app.callback(
    Output('dropdown_saved_files', 'options'),
    [
        Input('interval-component', 'n_intervals'),
    ]
)
def populate_dropdown(n_int):
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
        # Generate graph
        return gen_plot_saved(file_names)
    else: # Live
        return go.Figure()


def gen_plot_saved(file_names):

    data_cur = []

    if file_names is None:
        return

    for filename in file_names:

        df = pd.read_pickle('data/' + filename)

        for volt in df.columns[1:]:
            data_cur.append(go.Scatter(
                x = df["Time"],
                y = df[volt],
                name = str(volt) + " V",
                legendgroup =  filename
            ))

    fig_cur = go.Figure(
    data_cur,
    layout = go.Layout(
        xaxis=dict(title='Time (s)',range=[0, 100], gridwidth=1, zeroline=False),
        yaxis=dict(title='Current (mA/cm<sup>2</sup>)', range=[0, 60]),
        )
    )

    return fig_cur


        


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
)