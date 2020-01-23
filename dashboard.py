# -*- coding: utf-8 -*-
# for reading a file into dashboard
import base64
import datetime
import io

import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import pandas as pd 
import numpy as np 
import plotly.graph_objs as go
from plotly.subplots import make_subplots

#######################################################
# TODOList
# already have trip duration data so no need to calculate that column DONE
# allow upload of data DONE
# change boxplot to month plot DONE
# give plots different colors DONE
# explore some weather relationships with temperature and attribute DONE
#######################################################

# load the dataset 
bike_df = pd.read_csv('data.csv', nrows=200000)
time_data = pd.DataFrame(bike_df[['month', 'day', 'hour']])
# month data
months = bike_df['month'].value_counts().sort_index().reset_index()
months_x = months['index'].values
months_y = months['month']
# day of the week data
days = bike_df['day'].value_counts().sort_index().reset_index()
days_x = days['index'].values
days_y = days['day']
# hour data
hours = bike_df['hour'].value_counts().sort_index().reset_index()
hours_x = hours['index'].values
hours_y = hours['hour']

# create a sample data set to display in data
data_sample = pd.DataFrame(bike_df.sample(n=100))

# available time horizons for average trip duration plot
available_times = ['hour', 'day', 'month']

# dictionary that maps numbers to days of the week
day_names = {0:'Monday', 1:'Tuesday', 2:'Wednesday', 3:'Thursday', 4:'Friday', 5:'Saturday', 6:'Sunday'}
month_names = {0:'January', 1:'February', 2:'March', 3:'April', 4:'May', 5:'June', 6:'July', 7:'August',
               8:'September', 9:'October', 10:'November', 11:'December' }

# set of colors to use for boxplots
N_month = 12
colors_month = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(0, 360, N_month)]
N_hours = 24
colors_hour = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(0, 360, N_hours)]
N_days = 7
colors_day = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(0, 360, N_days)]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# for deployment
server = app.server

app.layout = html.Div([
    # Big title of the page
    html.Div([
        html.H1(children='Bike Sharing Rides in Chicago')
    ], style={'textAlign': 'center'}),
    dcc.Tabs([
        # give a view of the data in the data tab
        dcc.Tab(label='Data', children=[
            html.Div([
                dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'   
                },
        # Allow multiple files to be uploaded
        multiple=True
        ),
        html.Div(id='output-data-upload')
        ])
        ]),
        # present the analysis in the analysis tab
        dcc.Tab(label='Analysis', children=[
    # TAB with two other tabs as children 
    dcc.Tabs([
        dcc.Tab(label='Month', children=[
            html.Div([
                dcc.RadioItems(id='year-buttons',
                    options=[
                        {'label': '2014', 'value': 2014},
                        {'label': '2015', 'value': 2015},
                        {'label': '2016', 'value': 2016},
                        {'label': '2017', 'value': 2017}
                    ],
                    value=2015,
                    labelStyle={'display': 'inline-block'}
                )
            ], style={'width': '33%', 'align-items': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft':10}),  
            dcc.Graph(id='months-rides-temp')
        ]),
        # one child tab
        dcc.Tab(label='Days', children=[
            dcc.Graph(
                figure={
                    'data': [
                        {'x': [day_names[i] for i in range(7)], 'y': days_y,
                            'type': 'bar', 'name': 'Days', 'marker':dict(color=colors_day), 
                             },
                    ],
                    'layout': {
                        'title': 'Number of bike rides per day of the week',
                        'yaxis':{'title':'Number of bike rides'}
                    }
                }
            )
        ]),
        # another child tab
        dcc.Tab(label='Hours', children=[
            dcc.Graph(
                figure={
                    'data': [
                        {'x': hours_x, 'y': hours_y,
                            'type': 'bar', 'name': 'Hour', 'marker':dict(color=colors_hour)},
                    ],
                    'layout': {
                        'title': 'Number of bike rides per hour of the day',
                        'yaxis':{'title':'Number of bike rides'}
                }
                }
            )
        ]),
    ]),
    ### maps are commented out because they dont work during deployment
    # two tabs for the maps
    #dcc.Tabs([
    #    dcc.Tab(label='Visualization of rides', children=[
    #html.Iframe(id='map', srcDoc=open('chicago_map.html', 'r').read(), width='100%', height='400'),
    #    ]),
    #dcc.Tab(label='Visualization of Top 10 Routes', children=[
    #html.Iframe(id='routeMap', srcDoc=open('chiTopRoutes.html', 'r').read(), width='100%', height='400')
    #]),
    #]),

    # plot a graph with a slider and dropdown menu through callbacks
    # the dropdown menu
    # make two tabs for the callback graph that updates and one for the 
    # box-whisker plot
    dcc.Tabs([
        dcc.Tab(label='Average bike trip duration', children=[
            html.Div([
            dcc.Dropdown(
                id='time_horizon',
                options=[{'label': i, 'value': i} for i in available_times],
                optionHeight=50,
                # default display is day
                value='day'
            )], style={'width': '50%', 'display': 'inline-block'}),
            # slider to choose for which year data should be displayed
            # and that is used by the plot in each tab above
            html.Div([
            dcc.RadioItems(
                id='year_radio',
                options=[
                        {'label': '2014', 'value': 2014},
                        {'label': '2015', 'value': 2015},
                        {'label': '2016', 'value': 2016},
                        {'label': '2017', 'value': 2017}
                    ],
                    value=2015,
                    labelStyle={'display': 'inline-block'}
                )
            ], style={'width': '33%', 'align-items': 'center', 'marginBottom': 50, 'marginTop': 25, 'marginLeft':10}),
            # the graph created with an id that will be implemented in a callback
            dcc.Graph(id='average-trip-duration')
        ]),
        dcc.Tab(label='Box plot', children=[
            html.Div([
            dcc.RangeSlider(
                id='month-slider',
                marks={i: month_names[i] for i in range(0,12)},
                min = 0,
                max = 11,
                value =[0, 11]
            )], style={'width': '50%', 'padding-left':'48%', 'marginBottom': 50, 'marginTop': 25, 'marginRight':10}),
            
            dcc.Graph(id='month-box-plots')
        ])
    ]) 
    
    ]) # closes the analysis tab
    ]) # closes the big tab that creates data and analysis
])

# create a call back for the month number of rides graph
@app.callback(
    # Output is the graph with id
    Output('months-rides-temp', 'figure'),
    # Input will be RadioItem buttons
    [Input('year-buttons', 'value')])

def update_month_rides(year_radio):
    # filter the df based on year
    rides_by_year = bike_df[bike_df['year']==year_radio]
    # get number of rides per month
    months_rides = rides_by_year['month'].value_counts().sort_index().reset_index()
    months_rides_y = months_rides['month']
    # get the mean temperature per month
    months_temp = rides_by_year.groupby(['month'])['temperature'].mean().reset_index()
    month_temp_y = months_temp['temperature']
    # collect traces
    traces = []
    #figure = make_subplots(rows=1, cols=1, shared_xaxes=True, shared_yaxes=False)
    # add the ride data
    traces.append(go.Bar(
        x = [month_names[i] for i in range(12)],
        y = months_rides_y,
        name = '# of bike rides'
        ))
    # append the temperature data
    traces.append(go.Scatter(
        x = [month_names[i] for i in range(12)],
        y = month_temp_y,
        name = 'Mean Temperature', 
        yaxis= 'y2'
        ))
    figure = go.Figure(data=traces, 
                        layout={'title': 'Number of rides per month and average temperature', 'yaxis':{'title':'Number of rides', 'showgrid': False},
                                'yaxis2': {'title': 'Temperature in Fahrenheit', 'overlaying': 'y', 'side': 'right', 'showgrid': False}})
    return figure

# call back for average trip duratoin graph
@app.callback(
    # Output is the graph with the id
    Output('average-trip-duration', 'figure'),
    # Input is the different data depending on whether we use hour/day/month and a slider for the year
    [Input('time_horizon', 'value'),
     Input('year_radio', 'value')])

# function to update the average trip duration plot
def update_graph(time_horizon_value, year_slider_value):
    # filter the df based on the year
    df_by_year = bike_df[bike_df['year']==year_slider_value]
    # calculate the means for the different time-horizons
    # split into female and male
    male_df = df_by_year[df_by_year['gender']=='Male']
    female_df = df_by_year[df_by_year['gender']=='Female']
    # use the time_horizon_value as the groupby 
    #average_duration_time = df_update_bike.groupby([time_horizon_value])['trip_duration_minutes'].mean().reset_index()
    average_duration_time_m = male_df.groupby([time_horizon_value])['tripduration'].mean().reset_index()
    average_duration_time_f = female_df.groupby([time_horizon_value])['tripduration'].mean().reset_index()
    # get x values, if month or day display actual names
    if time_horizon_value == 'day':
        x_values_m = [day_names[d] for d in range(7)]
        x_values_f = [day_names[d] for d in range(7)]
    elif time_horizon_value == 'month':
        x_values_m = [month_names[m] for m in range(12)]
        x_values_f = [month_names[m] for m in range(12)]
    else:
        x_values_m = average_duration_time_m[time_horizon_value]
        x_values_f = average_duration_time_f[time_horizon_value]
    # get trip duration y values for each gender
    y_values_m = average_duration_time_m['tripduration']
    y_values_f = average_duration_time_f['tripduration']
    # create the figure
    figure = go.Figure(data=[
        go.Bar(name='male', x=x_values_m, y=y_values_m),
        go.Bar(name='female', x=x_values_f, y=y_values_f)],
        layout={'title': 'Average trip duration in minutes', 'yaxis':{'title': 'Duration in minutes'}, 'barmode':'group'})
   
    return figure

@app.callback(
    Output('month-box-plots', 'figure'),
    [Input('month-slider', 'value')]
)
def update_box_plot(month):
    # value of the slider is returned as list of two values and have to filter the 
    # data set accordingly 
    low = month[0]
    high = month[1]
    # filter the df based on the year
    df_by_year = bike_df[bike_df['year']==2017]
    traces = []
    # use the dictionary for days of the week and a day track
    month_track = month[0]
    # define traces for each day
    for m in range(low, high+1):
        df_by_year_and_month = df_by_year[df_by_year['month']==m+1]
        traces.append(go.Box(
            y=df_by_year_and_month['temperature'],
            boxpoints=False,
            name= month_names[month_track],
            marker=dict(
                color = colors_month[m],
            line = dict(
                color = colors_month[m])
        )))
        # increase low to next day
        month_track += 1
    figure = go.Figure(data=traces, layout={'title': 'Box Plots for monthly temperatures', 'yaxis':{'title':'Temperature in Fahrenheit'}})
    return figure

##############
# functions and callback to to load data
def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns], 
            style_table={'overflowX': 'scroll'}
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run_server(debug=True)
