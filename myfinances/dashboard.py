import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, dependencies, html

from myfinances.monthly_costs import MonthlyCosts

# px.defaults.template = 'plotly_dark'


class Dashboard:
    def __init__(self, monthly_costs: MonthlyCosts) -> None:
        self.app: Dash = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
        self.monthly_costs: MonthlyCosts = monthly_costs
        self.colors = {'background': '#111111', 'text': '#7FDBFF'}
        self.app.layout = html.Div(
            # style={'backgroundColor': self.colors['background']},
            children=[
                html.H1(
                    children='Finances Overview',
                    # style={'textAlign': 'center', 'color': self.colors['text']},
                ),
                dcc.Graph(
                    id='expenses-bar',
                ),
                html.Div(
                    children=[
                        dcc.Dropdown(
                            self.monthly_costs.get_months_to_analyze(),
                            self.monthly_costs.get_months_to_analyze()[0],
                            id='begin-dropdown',
                        ),
                        dcc.Dropdown(
                            self.monthly_costs.get_months_to_analyze(),
                            self.monthly_costs.get_months_to_analyze()[-1],
                            id='end-dropdown',
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        dcc.Graph(
                            id='label_pie',
                            style={'display': 'inline-block', 'width': '50%'},
                        ),
                        dcc.Graph(
                            id='sublabel_pie',
                            style={'display': 'inline-block', 'width': '50%'},
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.Label(
                            id='available_amount',
                        ),
                    ]
                ),
                dcc.Graph(
                    id='income_pie',
                ),
            ],
        )
        (  # type: ignore
            self.app.callback(
                dependencies.Output('available_amount', 'children'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.available_amount),
            self.app.callback(
                dependencies.Output('label_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_label_pie),
            self.app.callback(
                dependencies.Output('income_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_income_pie),
            self.app.callback(
                dependencies.Output('sublabel_pie', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_sublabel_pie),
            self.app.callback(
                dependencies.Output('expenses-bar', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_expenses_bar),
        )

    def available_amount(self, *_) -> str:
        return f'Available: {self.monthly_costs.get_averaged_expenses_by_label().sum()}'

    def plot_label_pie(self, *_) -> go.Figure:  # noqa: N803
        figure: go.Figure = px.pie(
            self.monthly_costs.get_averaged_expenses_by_label()
            .drop('Einkommen')
            .mul(-1)
            .reset_index(),
            values='Amount',
            names='Label',
        )

        return figure

    def plot_sublabel_pie(self, clickData, *_) -> go.Figure:  # noqa: N803
        label = 'Sonstiges'
        if clickData:
            label: str = clickData['points'][0]['label']
        figure: go.Figure = px.pie(
            self.monthly_costs.get_averaged_expenses_by_sublabel(label).mul(-1).reset_index(),
            values='Amount',
            names='Sublabel',
        )
        return figure

    def plot_income_pie(self, *_) -> go.Figure:  # noqa: N803
        figure: go.Figure = px.pie(
            self.monthly_costs.get_averaged_income(), values='Amount', names='Sublabel'
        )
        return figure

    def plot_expenses_bar(self, begin_dropdown_data, end_dropdown_data) -> go.Figure:  # noqa: N803
        self.monthly_costs.set_date_to_start(pd.to_datetime(begin_dropdown_data))
        self.monthly_costs.set_date_to_end(pd.to_datetime(end_dropdown_data))
        figure: go.Figure = px.bar(
            self.monthly_costs.get_monthly_expenses(),
            x='Date',
            y='Amount',
            color='Amount',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
        )
        return figure

    def run(self) -> None:
        self.app.run(debug=True)
