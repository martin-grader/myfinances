import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, ctx, dash_table, dcc, dependencies, html

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_costs import MonthlyCosts
from myfinances.utils import get_next_month, get_previous_day

# px.defaults.template = 'plotly_dark'


class Dashboard:
    def __init__(self, monthly_costs: MonthlyCosts) -> None:
        # self.app: Dash = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
        self.app: Dash = Dash(__name__)
        self.monthly_costs: MonthlyCosts = monthly_costs
        # self.colors = {'background': '#111111', 'text': '#7FDBFF'}
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
                            # options=self.monthly_costs.get_months_to_analyze_start(),
                            id='begin-dropdown',
                        ),
                        dcc.Dropdown(
                            options=self.monthly_costs.get_months_to_analyze_end(),
                            id='end-dropdown',
                        ),
                        dcc.Dropdown(
                            options=list(range(1, 28)),
                            value=self.monthly_costs.get_month_split_day(),
                            id='month-split-date',
                        ),
                        html.Button('Reset', id='reset-dates'),
                        html.Details(
                            dcc.Checklist(
                                sorted(self.monthly_costs.get_all_labels()),
                                self.monthly_costs.get_active_labels(),
                                id='labels-checklist',
                            )
                        ),
                        html.Button('Apply', id='apply-labels', n_clicks=0),
                    ]
                ),
                html.Div(
                    children=[
                        html.Details(
                            [
                                html.Summary(key),
                                html.Div(
                                    children=[
                                        dcc.Checklist(
                                            values,
                                            self.monthly_costs.get_active_sublabels(key),
                                            id=f'{key}',
                                        )
                                    ],
                                ),
                            ],
                        )
                        for key, values in self.monthly_costs.get_all_sublabels().items()
                    ],
                    style={'display': 'flex', 'flexDirection': 'row'},
                ),
                html.Div(
                    children=[
                        dcc.Graph(
                            id='label_pie',
                            style={'display': 'inline-block', 'width': '30%'},
                        ),
                        dcc.Graph(
                            id='sublabel_pie',
                            style={'display': 'inline-block', 'width': '30%'},
                        ),
                        dcc.Graph(
                            id='income_pie',
                            style={'display': 'inline-block', 'width': '30%'},
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        dcc.Graph(
                            id='label_line',
                            style={'display': 'inline-block', 'width': '30%'},
                        ),
                        dcc.Graph(
                            id='sublabel_line',
                            style={'display': 'inline-block', 'width': '30%'},
                        ),
                        dcc.Graph(
                            id='income_line',
                            style={'display': 'inline-block', 'width': '30%'},
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.Label(
                            id='available_amount',
                        ),
                        html.Details(
                            [
                                html.Summary('Alle Überweisungen'),
                                dash_table.DataTable(
                                    sort_action='native',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    id='all-data',
                                ),
                            ],
                        ),
                        html.Details(
                            [
                                html.Summary('Überweisungen: Label'),
                                dash_table.DataTable(
                                    sort_action='native',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    id='label-data',
                                ),
                            ],
                        ),
                        html.Details(
                            [
                                html.Summary('Überweisungen: Sublabel'),
                                dash_table.DataTable(
                                    sort_action='native',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    id='sublabel-data',
                                ),
                            ],
                        ),
                    ],
                    style={'width': '90vw', 'margin': 'auto'},
                ),
            ],
        )
        (  # type: ignore
            self.app.callback(
                inputs={
                    'apply_labels': dependencies.Input('apply-labels', 'n_clicks'),
                    'labels': dependencies.Input('labels-checklist', 'value'),
                    'sublabels': {
                        key: dependencies.Input(key, 'value')
                        for key in self.monthly_costs.get_all_labels()
                    },
                }
            )(self.set_active_labels),
            self.app.callback(
                dependencies.Output('begin-dropdown', 'value'),
                dependencies.Output('begin-dropdown', 'options'),
                dependencies.Input('expenses-bar', 'clickData'),
                dependencies.Input('month-split-date', 'value'),
                dependencies.Input('reset-dates', 'n_clicks'),
                dependencies.Input('apply-labels', 'n_clicks'),
            )(self.begin_dropdown),
            self.app.callback(
                dependencies.Output('end-dropdown', 'value'),
                dependencies.Output('end-dropdown', 'options'),
                dependencies.Input('expenses-bar', 'clickData'),
                dependencies.Input('month-split-date', 'value'),
                dependencies.Input('reset-dates', 'n_clicks'),
                dependencies.Input('apply-labels', 'n_clicks'),
            )(self.end_dropdown),
            self.app.callback(
                dependencies.Output('all-data', 'data'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.all_data),
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
                dependencies.Output('label_line', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_label_line_chart),
            self.app.callback(
                dependencies.Output('sublabel_line', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('sublabel_pie', 'clickData'),
                dependencies.Input('sublabel_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_sublabel_line_chart),
            self.app.callback(
                dependencies.Output('income_line', 'figure'),
                dependencies.Input('income_pie', 'clickData'),
                dependencies.Input('income_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_income_line_chart),
            self.app.callback(
                dependencies.Output('expenses-bar', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_expenses_bar),
            self.app.callback(
                dependencies.Output('label-data', 'data'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.label_data),
            self.app.callback(
                dependencies.Output('sublabel-data', 'data'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('sublabel_pie', 'clickData'),
                dependencies.Input('sublabel_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.sublabel_data),
        )

    def set_month_split_day(self, month_split_day) -> None:
        self.monthly_costs.set_month_split_day(month_split_day)

    def set_active_labels(self, apply_labels, labels, sublabels) -> None:
        if apply_labels > 0:
            sublabels_to_set = {k: v for k, v in sublabels.items() if k in labels}
            self.monthly_costs.set_active_sublabels(sublabels_to_set)

    def begin_dropdown(
        self,
        click_data,
        month_split_day,
        *_,
    ) -> tuple[pd.Timestamp, list[pd.Timestamp]]:  # noqa N803
        if 'reset-dates' == ctx.triggered_id:
            value: pd.Timestamp = self.monthly_costs.get_min_date_to_start()
        elif 'expenses-bar' == ctx.triggered_id:
            clicked_date = pd.to_datetime(click_data['points'][0]['label'])
            value: pd.Timestamp = pd.Timestamp(
                year=clicked_date.year, month=clicked_date.month, day=month_split_day
            )  # type: ignore
        elif 'month-split-date' == ctx.triggered_id:
            self.monthly_costs.set_month_split_day(month_split_day)
            value: pd.Timestamp = self.monthly_costs.get_min_date_to_start()
        else:
            value: pd.Timestamp = self.monthly_costs.get_months_to_analyze_start()[0]  # type: ignore
        options: list[pd.Timestamp] = self.monthly_costs.get_all_months_to_analyze_start()
        return (value, options)

    def end_dropdown(
        self,
        click_data,
        month_split_day,
        *_,
    ) -> tuple[pd.Timestamp, list[pd.Timestamp]]:
        if 'reset-dates' == ctx.triggered_id:
            value: pd.Timestamp = self.monthly_costs.get_max_date_to_end()
        elif 'expenses-bar' == ctx.triggered_id:
            clicked_date = pd.to_datetime(click_data['points'][0]['label'])
            value: pd.Timestamp = pd.Timestamp(
                year=clicked_date.year, month=clicked_date.month, day=month_split_day
            )  # type: ignore
            value = get_previous_day(get_next_month(value))
        elif 'month-split-date' == ctx.triggered_id:
            self.monthly_costs.set_month_split_day(month_split_day)
            value: pd.Timestamp = self.monthly_costs.get_max_date_to_end()
        else:
            value: pd.Timestamp = self.monthly_costs.get_months_to_analyze_end()[-1]  # type: ignore
        options: list[pd.Timestamp] = self.monthly_costs.get_all_months_to_analyze_end()
        return (value, options)

    def all_data(self, *_) -> list[dict]:
        return self.monthly_costs.get_transactions().to_dict('records')

    def label_data(self, click_data, figure_pie, *_) -> list[dict]:
        label, _ = self.get_active_label_and_color(click_data, figure_pie)
        df = self.monthly_costs.get_transactions()
        df: pd.DataFrame = df.loc[df[TransactionLabeled.Label] == label]
        return df.to_dict('records')

    def sublabel_data(
        self, click_data_label, figure_pie_label, click_data_sublabel, figure_pie, *_
    ) -> list[dict]:
        label, _ = self.get_active_label_and_color(click_data_label, figure_pie_label)
        sublabel, _ = self.get_active_sublabel_and_color(click_data_sublabel, figure_pie)
        df = self.monthly_costs.get_transactions()
        df: pd.DataFrame = df.loc[
            (df[TransactionLabeled.Label] == label) & (df[TransactionLabeled.Sublabel] == sublabel)
        ]
        print(df)
        return df.to_dict('records')

    def available_amount(self, click_data, figure_pie, *_) -> str:
        return f'Available: {self.monthly_costs.get_averaged_expenses_by_label().sum()}'

    def plot_label_pie(self, *_) -> go.Figure:
        active_labels = self.monthly_costs.get_active_labels()
        if 'Einkommen' in active_labels:
            figure: go.Figure = px.pie(
                self.monthly_costs.get_averaged_expenses_by_label()
                .drop('Einkommen')
                .mul(-1)
                .reset_index(),
                values='Amount',
                names='Label',
            )
        else:
            figure: go.Figure = px.pie(
                self.monthly_costs.get_averaged_expenses_by_label().mul(-1).reset_index(),
                values='Amount',
                names='Label',
            )

        return figure

    def plot_sublabel_pie(self, click_data, *_) -> go.Figure:
        label = 'Sonstiges'
        if click_data:
            label: str = click_data['points'][0]['label']
        figure: go.Figure = px.pie(
            self.monthly_costs.get_averaged_expenses_by_sublabel(label).mul(-1).reset_index(),
            values='Amount',
            names='Sublabel',
        )
        return figure

    def plot_income_pie(self, *_) -> go.Figure:
        figure: go.Figure = px.pie(
            self.monthly_costs.get_averaged_income().reset_index(),
            values='Amount',
            names='Sublabel',
        )
        return figure

    def plot_label_line_chart(self, click_data, figure_pie, *_) -> go.Figure:
        label, color = self.get_active_label_and_color(click_data, figure_pie)
        df = self.monthly_costs.get_monthly_expenses_by_label(label)
        df.loc[:, 'Amount'] = df.loc[:, 'Amount'] * -1
        mean: float = self.monthly_costs.get_averaged_expenses_by_label().loc[label] * -1

        figure: go.Figure = self.create_line_plot_figure(df, mean, label, color)
        return figure

    def get_active_label_and_color(self, click_data, figure_pie) -> tuple[str, str]:
        label: str = figure_pie['data'][0]['labels'][0]
        color: str = figure_pie['layout']['template']['layout']['colorway'][0]
        if click_data:
            label: str = click_data['points'][0]['label']
            color = click_data['points'][0]['color']
        return label, color

    def get_active_sublabel_and_color(self, click_data_sublabel, figure_pie) -> tuple[str, str]:
        all_sublabels: list[str] = figure_pie['data'][0]['labels']
        default_sublabel = all_sublabels[0]
        default_color: str = figure_pie['layout']['template']['layout']['colorway'][0]

        if click_data_sublabel:
            sublabel: str = click_data_sublabel['points'][0]['label']
            color: str = click_data_sublabel['points'][0]['color']
            if sublabel not in all_sublabels:
                sublabel: str = default_sublabel
                color = default_color
        else:
            sublabel: str = default_sublabel
            color = default_color
        return sublabel, color

    def plot_sublabel_line_chart(
        self, click_data_label, figure_pie_label, click_data_sublabel, figure_pie, *_
    ) -> go.Figure:
        label, _ = self.get_active_label_and_color(click_data_label, figure_pie_label)
        sublabel, color = self.get_active_sublabel_and_color(click_data_sublabel, figure_pie)

        df = self.monthly_costs.get_monthly_expenses_by_sublabel(label, sublabel)
        df.loc[:, 'Amount'] = df.loc[:, 'Amount'] * -1
        mean: float = self.monthly_costs.get_averaged_expenses_by_sublabel(label).loc[sublabel] * -1
        figure: go.Figure = self.create_line_plot_figure(df, mean, sublabel, color)
        return figure

    def plot_income_line_chart(self, click_data, figure_pie, *_) -> go.Figure:
        label = 'Einkommen'
        sublabel: str = figure_pie['data'][0]['labels'][0]
        color: str = figure_pie['layout']['template']['layout']['colorway'][0]
        if click_data:
            sublabel: str = click_data['points'][0]['label']
            color: str = click_data['points'][0]['color']

        df = self.monthly_costs.get_monthly_expenses_by_sublabel(label, sublabel)
        mean: float = self.monthly_costs.get_averaged_income().loc[sublabel]

        figure: go.Figure = self.create_line_plot_figure(df, mean, sublabel, color)

        return figure

    def plot_expenses_bar(self, begin_dropdown_data, end_dropdown_data, *_) -> go.Figure:
        self.monthly_costs.set_start_and_end_date(
            pd.to_datetime(begin_dropdown_data), pd.to_datetime(end_dropdown_data)
        )
        if self.monthly_costs.get_n_months_to_analyze() == 1:
            df: pd.DataFrame = self.monthly_costs.get_daily_expenses()
        else:
            df: pd.DataFrame = self.monthly_costs.get_monthly_expenses()
        figure: go.Figure = px.bar(
            data_frame=df,
            x='Date',
            y='Amount',
            color='Amount',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
        )
        return figure

    def create_line_plot_figure(self, df, mean: float, title: str, color: str) -> go.Figure:
        figure: go.Figure = px.line(
            data_frame=df,
            x='Date',
            y='Amount',
            title=title,
            markers=True,
            color_discrete_sequence=[color],
        )
        figure.add_hline(
            mean, line_dash='dot', line_color=color, annotation_text=f'Mittel: {mean:.0f}'
        )
        return figure

    def run(self) -> None:
        self.app.run(debug=True)
