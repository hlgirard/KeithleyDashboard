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
                    style={'width': '100px', 'margin': 'auto'},
                    value=False,
                )
            ], className="col-2"),
            
            # Dropdown to select saved data to display
            html.Div([
                dcc.Dropdown(
                    id='dropdown_saved_files',
                    options = [
                        {'label': 'placeholder', 'value': 'placeholder'}
                    ],
                    value = ['placeholder'],
                )
            ], className = "col-5"),

            # Empty div to separated
            html.Div(className = "col-2"),

            # Mode selector
            html.Div([
                html.H2(
                    'Mode',
                    style = {'font-family': 'Helvetica'},
                ),
                daq.ToggleSwitch(
                    id='toggle_constant_feedback',
                    label=['Constant', 'Feedback'],
                    style={'width': '100px'},
                    value = 'Constant',
                )
            ], style = {'float': 'left'}, className = "col-3")

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

        # Parameter selection
        html.Div([
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
            html.Label('Autostop', style = {'margin-top' : '20'}),
            html.Br(),
            daq.ToggleSwitch(
                id = "toggle_autostop",
                label = ["Off", "On"],
                style = {'width': '100px'},
                value = 'Off',
            )
        ], className = "col-3")
    ], id = "div_parameter_selection", className = "row"),

    # Instrument connection
    html.Div([

        # Connect button
        html.Div([
            daq.PowerButton(
                id = "button_instrument_connect",
                on = False,
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

    ], className = 'row')

])


#############################################
# Interaction Between Components / Controller
#############################################




# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
)