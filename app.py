import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from flask_caching import Cache

boss_list = [
    'flauros',
    'forneus',
    'barbatos',
    'halphas',
    'amon_ra',
    'sabnock',
    'andromalius'
]
boss_color = {
    'flauros': '#d62728',
    'forneus': '#9467bd',
    'barbatos': '#1f77b4',
    'halphas': '#ff7f0e',
    'amon_ra': '#bcbd22',
    'sabnock': '#7f7f7f',
    'andromalius': '#e377c2'
}
boss_name = {
    'flauros':'Flauros',
    'forneus': 'Forneus',
    'barbatos': 'Barbatos',
    'halphas': 'Halphas',
    'amon_ra': 'Amon Ra',
    'sabnock': 'Sabnock',
    'andromalius': 'Andromalius'
}
boss_interval = {
    'flauros': 4,
    'forneus': 4,
    'barbatos': 1,
    'halphas': 8,
    'amon_ra': 8,
    'sabnock': 4,
    'andromalius': 3,
    'all_kps': 8,
    'all_kps_except_barbatos': 8,
    'all_kills_counts': 8
}
chart_dict = {
    'kps': {'name': 'KPS', 'unit': 'Kills per second'},
    'hp': {'name': 'Kills Counts', 'unit': 'Kills'}
}

boss_df = {}
for boss in boss_list:
    boss_df[boss] = pd.read_csv('output/{}.csv'.format(boss))
#update_time = pd.to_datetime(boss_df['andromalius']['time'].iloc[-1])

dash_boss = [{'value': boss_id, 'label': name} for boss_id, name in boss_name.items()]
dash_chart = [{'value': chart, 'label': chart_dict[chart]['name']} for chart in chart_dict]

app = dash.Dash(__name__)
app.title = "NA Solomon raid statistic"
cache = Cache(app.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379'
})
app.config.suppress_callback_exceptions = True
timeout = 3600 #cache timeout in seconds
server = app.server

app.layout = html.Div(children=[
    html.H1(children='NA Solomon raid statistic', style={'textAlign': 'center'}),
    html.Div(children=[
        html.Div(children=[
            html.Div(children='Boss:', style={'font-weight': 'bold', 'display': 'inline-block'}),
            dcc.Checklist(
                id='boss_checklist',
                options=dash_boss,
                labelStyle={'display': 'inline-block'},
                values=[b for b in boss_list if b != 'barbatos'],
                style={'display': 'inline-block', 'margin-left': '5px'}
            )
        ]),
        html.Div(children=[
            html.Div(children='Statistic:', style={'font-weight': 'bold', 'display': 'inline-block'}),
            dcc.RadioItems(
                id='chart_value',
                options=dash_chart,
                labelStyle={'display': 'inline-block'},
                value='kps',
                style={'display': 'inline-block', 'margin-left': '5px'}
            )
        ]),
        dcc.Graph(id='solomon_raid_graph', style={'height': '75vh'})
    ], style={'textAlign': 'center'})
]#, className="container"
)

@app.callback(
    dash.dependencies.Output('solomon_raid_graph', 'figure'),
    [dash.dependencies.Input('boss_checklist', 'values'),
    dash.dependencies.Input('chart_value', 'value')]
)
@cache.memoize(timeout=timeout)
def update_graph(chosen_boss, chosen_chart):
    if len(chosen_boss) == 1:
        boss_title = boss_name[chosen_boss[0]]
    else:
        boss_title = 'Demon God Pillars'
    chart_list = []
    for boss in chosen_boss:
        time = boss_df[boss]['time']
        chart_list.append(
            go.Scatter(
                x = time,
                y = boss_df[boss][chosen_chart],
                name = boss_name[boss],
                line = dict(color = boss_color[boss])
            )
        )
    layout = dict(
        title = '{} {}'.format(boss_title, chart_dict[chosen_chart]['name']),
        xaxis = dict(
            title = 'Pacific Standard Time',
            rangeselector=dict(
                buttons=list([
                    dict(count=12,
                        label='12h',
                        step='hour',
                        stepmode='backward'),
                    dict(count=1,
                        label='1d',
                        step='day',
                        stepmode='backward'),
                    dict(count=3,
                        label='3d',
                        step='day',
                        stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(
                visible = True
            ),
            type='date'
        ),
        yaxis = dict(
            title = chart_dict[chosen_chart]['unit']
        )
    )
    return {
        'data': chart_list,
        'layout': layout
    }

if __name__ == '__main__':
    app.run_server(debug=True)
