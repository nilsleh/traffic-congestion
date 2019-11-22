import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd

traffic_df = pd.read_csv('trafficData.csv')
available_cities = traffic_df['City'].unique()
atlanta = traffic_df[traffic_df['City'] == 'Atlanta']
weekend_atl = atlanta[atlanta['Weekend']==1]
weekday_atl = atlanta[atlanta['Weekend']==0]
weekday_atl_hour = weekday_atl.groupby('Hour')['TotalTimeStopped_p80'].mean().reset_index()
weekend_atl_hour = weekend_atl.groupby('Hour')['TotalTimeStopped_p80'].mean().reset_index()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# colors for background and text
colors = {
    'background': '#f2f2f2',
    'text': '#322ea3'
}

# begin the app layout and graphic
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    # this creates a header
    html.H1(children='Traffic Congestion Dashboard',
            style={'textAlign': 'center',
                   'color': colors['text']}
            ),
    # can create a subtitle
    html.Div(children='''
        A visualization of traffic data in four major cities
    ''',  style={
        'textAlign': 'center',
        'color': colors['text']}),
    # create a graph
    dcc.Graph(
        # id for the graph
        id='example-graph',
        figure={
            # data to plot
            'data': [
                {'x': weekday_atl_hour['Hour'], 'y': weekday_atl_hour['TotalTimeStopped_p80'], 'type': 'bar', 'name': 'Weekday'},
                {'x': weekend_atl_hour['Hour'], 'y': weekend_atl_hour['TotalTimeStopped_p80'], 'type': 'bar', 'name': 'Weekend'},
            ],
            # create background color and title for the graph
            'layout': {
                'title': 'Atlanta Waiting times',
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                        'color': colors['text']
                }
           }
        }
    ),
    # create a title for the second graph:
    html.Div(children='''
        Distribution of stop times 
    ''',  style={
        'textAlign': 'center',
        'color': colors['text']}),
    # create a second graph below
    # first create radio items buttons to select the city
    dcc.RadioItems(id='city-buttons',
                 options=[{'label': city, 'value': city} for city in available_cities],
                 value='City',
                 #labelStyle={'display': 'inline-bloc'}
                   ),
    # call the graph with the id
    dcc.Graph(id='stop-times-dist-cities')

])

# create a callback to make the graph interactable
@app.callback(
    Output('stop-times-dist-cities', 'figure'),
    [Input('city-buttons', 'value')])
# function to update stop-times-distribution
def update_stop_dist_city(selected_city):
    city_traffic_df = traffic_df[traffic_df['City'] == selected_city]
    traces = [dict(
        x=city_traffic_df['Hour'],
        y=city_traffic_df['TotalTimeStopped_p80'],
        mode='markers',
        opacity=0.5
    )]
    return {
        'data':traces,
        'layout': dict(
            xaxis={'title': 'Hour of the day'},
            yaxis={'title': 'Stop time in seconds'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            hovermode='closest'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=False)
