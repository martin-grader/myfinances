import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, clientside_callback, ctx, dash_table, dcc, dependencies, html
from dash_bootstrap_templates import load_figure_template
from pandera.typing import DataFrame

from myfinances.label_data import TransactionLabeled
from myfinances.monthly_costs import MonthlyCosts
from myfinances.utils import get_next_month, get_previous_day


class Dashboard:
    def __init__(self, monthly_costs: MonthlyCosts) -> None:
        self.dbc_css = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css'
        self.theme = 'bootstrap'
        load_figure_template([self.theme, self.theme + '_dark'])  # type:ignore
        self.app: Dash = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP, self.dbc_css, dbc.icons.FONT_AWESOME],
        )
        self.monthly_costs: MonthlyCosts = monthly_costs
        self.color_mode_switch = html.Span(
            [
                dbc.Label(className='fa fa-moon', html_for='color-mode-switch'),
                dbc.Switch(
                    id='color-mode-switch',
                    value=False,
                    className='d-inline-block ms-1',
                    persistence=True,
                ),
                dbc.Label(className='fa fa-sun', html_for='color-mode-switch'),
            ]
        )
        self.monthly_transactions_plot = html.Div(
            [
                dcc.Graph(
                    id='monthly-transactions-plot',
                ),
            ]
        )
        self.date_control = dbc.Card(
            [
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label('Start:'),
                                        dcc.Dropdown(
                                            id='begin-dropdown',
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label('Ende:'),
                                        dcc.Dropdown(
                                            id='end-dropdown',
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label('Monatssplittag:'),
                                        dcc.Dropdown(
                                            options=list(range(1, 28)),
                                            value=self.monthly_costs.get_month_split_day(),
                                            id='month-split-date',
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button('Reset', id='reset-dates'),
                                    align='end',
                                ),
                            ]
                        )
                    ],
                ),
            ],
            body=True,
        )
        self.available_amount_card = dbc.Col(
            [
                dbc.Card(
                    [
                        dbc.CardHeader('Availabel amount'),
                        dbc.CardBody(
                            id='available_amount',
                        ),
                    ]
                ),
            ],
            width=1,
        )

        self.app.layout = dbc.Container(
            [
                html.H1(
                    children='Finances Overview',
                ),
                self.color_mode_switch,
                html.Div(
                    children=[
                        self.date_control,
                        self.monthly_transactions_plot,
                        self.available_amount_card,
                        html.Details(
                            dcc.Checklist(
                                options=sorted(self.monthly_costs.get_all_labels()),
                                value=self.monthly_costs.get_active_labels(),
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
                dbc.Tabs(
                    [
                        dbc.Tab(
                            [
                                dash_table.DataTable(
                                    sort_action='native',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    id='all-data',
                                ),
                            ],
                            label='All Transactions',
                        ),
                        dbc.Tab(
                            [
                                dash_table.DataTable(
                                    sort_action='native',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    id='label-data',
                                ),
                            ],
                            label='Transactions of selected label',
                        ),
                        dbc.Tab(
                            [
                                dash_table.DataTable(
                                    sort_action='native',
                                    style_data={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    id='sublabel-data',
                                ),
                            ],
                            label='Transactions of selected sublabel',
                        ),
                    ],
                    # className='dbc dbc-row-selectable',
                ),
            ],
            fluid=True,
            className='dbc',
        )
        (  # type: ignore
            self.app.callback(
                inputs={
                    'times_apply_button_pushed': dependencies.Input('apply-labels', 'n_clicks'),
                    'active_labels': dependencies.Input('labels-checklist', 'value'),
                    'active_sublabels': {
                        key: dependencies.Input(key, 'value')
                        for key in self.monthly_costs.get_all_labels()
                    },
                }
            )(self.set_active_labels),
            self.app.callback(
                dependencies.Output('begin-dropdown', 'value'),
                dependencies.Output('begin-dropdown', 'options'),
                dependencies.Input('monthly-transactions-plot', 'clickData'),
                dependencies.Input('month-split-date', 'value'),
                dependencies.Input('reset-dates', 'n_clicks'),
                dependencies.Input('apply-labels', 'n_clicks'),
            )(self.begin_dropdown),
            self.app.callback(
                dependencies.Output('end-dropdown', 'value'),
                dependencies.Output('end-dropdown', 'options'),
                dependencies.Input('monthly-transactions-plot', 'clickData'),
                dependencies.Input('month-split-date', 'value'),
                dependencies.Input('reset-dates', 'n_clicks'),
                dependencies.Input('apply-labels', 'n_clicks'),
            )(self.end_dropdown),
            self.app.callback(
                dependencies.Output('all-data', 'data'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.get_transactions_table),
            self.app.callback(
                dependencies.Output('available_amount', 'children'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.available_amount),
            self.app.callback(
                dependencies.Output('label_pie', 'figure'),
                dependencies.Input('color-mode-switch', 'value'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_transactions_by_label_pie),
            self.app.callback(
                dependencies.Output('income_pie', 'figure'),
                dependencies.Input('color-mode-switch', 'value'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_income_pie),
            self.app.callback(
                dependencies.Output('sublabel_pie', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('color-mode-switch', 'value'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_transactions_by_sublabel_pie),
            self.app.callback(
                dependencies.Output('label_line', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('color-mode-switch', 'value'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_label_line_chart),
            self.app.callback(
                dependencies.Output('sublabel_line', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('sublabel_pie', 'clickData'),
                dependencies.Input('sublabel_pie', 'figure'),
                dependencies.Input('color-mode-switch', 'value'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_sublabel_line_chart),
            self.app.callback(
                dependencies.Output('income_line', 'figure'),
                dependencies.Input('income_pie', 'clickData'),
                dependencies.Input('income_pie', 'figure'),
                dependencies.Input('color-mode-switch', 'value'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.plot_income_line_chart),
            self.app.callback(
                dependencies.Output('monthly-transactions-plot', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
                dependencies.Input('color-mode-switch', 'value'),
            )(self.plot_expenses_bar),
            self.app.callback(
                dependencies.Output('label-data', 'data'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.get_transactions_table_by_label),
            self.app.callback(
                dependencies.Output('sublabel-data', 'data'),
                dependencies.Input('label_pie', 'clickData'),
                dependencies.Input('label_pie', 'figure'),
                dependencies.Input('sublabel_pie', 'clickData'),
                dependencies.Input('sublabel_pie', 'figure'),
                dependencies.Input('begin-dropdown', 'value'),
                dependencies.Input('end-dropdown', 'value'),
            )(self.get_transactions_table_by_sublabel),
        )

    clientside_callback(
        """
    (switchOn) => {
       document.documentElement.setAttribute('data-bs-theme', switchOn ? 'light' : 'dark');
       return window.dash_clientside.no_update
    }
    """,
        Output('color-mode-switch', 'id'),
        Input('color-mode-switch', 'value'),
    )

    def set_month_split_day(self, month_split_day: int) -> None:
        self.monthly_costs.set_month_split_day(month_split_day)

    def set_active_labels(
        self,
        times_apply_button_pushed: int,
        active_labels: list[str],
        active_sublabels: dict[str, list[str]],
    ) -> None:
        if times_apply_button_pushed > 0:
            sublabels_to_set: dict[str, list[str]] = {
                label: sublabels
                for label, sublabels in active_sublabels.items()
                if label in active_labels
            }
            self.monthly_costs.set_active_sublabels(sublabels_to_set)

    def begin_dropdown(
        self,
        monthly_transactions_plot_click_data: dict,
        month_split_day: int,
        *_,
    ) -> tuple[pd.Timestamp, list[pd.Timestamp]]:
        if 'month-split-date' == ctx.triggered_id:
            self.monthly_costs.set_month_split_day(month_split_day)
        options: list[pd.Timestamp] = self.monthly_costs.get_all_months_to_analyze_start()
        value: pd.Timestamp = self.monthly_costs.get_min_date_to_start()
        if 'monthly-transactions-plot' == ctx.triggered_id:
            value: pd.Timestamp = extract_date_from_click_data(
                monthly_transactions_plot_click_data, month_split_day
            )
        return (value, options)

    def end_dropdown(
        self,
        monthly_transactions_plot_click_data: dict,
        month_split_day: int,
        *_,
    ) -> tuple[pd.Timestamp, list[pd.Timestamp]]:
        if 'month-split-date' == ctx.triggered_id:
            self.monthly_costs.set_month_split_day(month_split_day)
        options: list[pd.Timestamp] = self.monthly_costs.get_all_months_to_analyze_end()
        value: pd.Timestamp = self.monthly_costs.get_max_date_to_end()
        if 'monthly-transactions-plot' == ctx.triggered_id:
            first_day_last_month: pd.Timestamp = extract_date_from_click_data(
                monthly_transactions_plot_click_data, month_split_day
            )
            value: pd.Timestamp = get_previous_day(get_next_month(first_day_last_month))
        return (value, options)

    def get_transactions_table(self, *_) -> list[dict]:
        return self.monthly_costs.get_transactions().to_dict('records')

    def get_transactions_table_by_label(
        self,
        transactions_by_label_pie_click_data: dict,
        transactions_by_label_pie: dict,
        *_,
    ) -> list[dict]:
        label, _ = get_active_label_and_color(
            transactions_by_label_pie_click_data, transactions_by_label_pie
        )
        df: DataFrame[TransactionLabeled] = self.monthly_costs.get_transactions()
        return df.loc[df[TransactionLabeled.Label] == label].to_dict('records')

    def get_transactions_table_by_sublabel(
        self,
        transactions_by_label_pie_click_data: dict,
        transactions_by_label_pie: dict,
        transactions_by_sublabel_pie_click_data: dict,
        transactions_by_sublabel_pie: dict,
        *_,
    ) -> list[dict]:
        label, _ = get_active_label_and_color(
            transactions_by_label_pie_click_data, transactions_by_label_pie
        )
        sublabel, _ = get_active_sublabel_and_color(
            transactions_by_sublabel_pie_click_data, transactions_by_sublabel_pie
        )
        df: DataFrame[TransactionLabeled] = self.monthly_costs.get_transactions()
        return df.loc[
            (df[TransactionLabeled.Label] == label) & (df[TransactionLabeled.Sublabel] == sublabel)
        ].to_dict('records')

    def available_amount(self, *_) -> str:
        return f'{self.monthly_costs.get_averaged_expenses_by_label().sum():.2f} € '

    def plot_transactions_by_label_pie(self, theme, *_) -> go.Figure:
        df: pd.DataFrame = (
            self.monthly_costs.get_averaged_expenses_by_label()
            .drop('Einkommen', errors='ignore')
            .mul(-1)
            .reset_index()
        )
        figure: go.Figure = create_pie_plot_figure(df, TransactionLabeled.Label, theme)
        return figure

    def plot_transactions_by_sublabel_pie(
        self,
        transactions_by_label_pie_click_data: dict,
        transactions_by_label_pie: dict,
        theme,
        *_,
    ) -> go.Figure:
        label, _ = get_active_label_and_color(
            transactions_by_label_pie_click_data, transactions_by_label_pie
        )
        df: pd.DataFrame = (
            self.monthly_costs.get_averaged_expenses_by_sublabel(label).mul(-1).reset_index()
        )
        figure: go.Figure = create_pie_plot_figure(df, TransactionLabeled.Sublabel, theme)
        return figure

    def plot_income_pie(self, theme, *_) -> go.Figure:
        df: pd.DataFrame = (
            self.monthly_costs.get_averaged_income()
            .reset_index()
            .sort_values(by=TransactionLabeled.Amount, ascending=False)
        )
        figure: go.Figure = create_pie_plot_figure(df, TransactionLabeled.Sublabel, theme)
        return figure

    def plot_label_line_chart(
        self,
        transactions_by_label_pie_click_data: dict,
        transactions_by_label_pie: dict,
        dark_mode_off: bool,
        *_,
    ) -> go.Figure:
        label, color = get_active_label_and_color(
            transactions_by_label_pie_click_data, transactions_by_label_pie
        )
        df: pd.DataFrame = self.monthly_costs.get_monthly_expenses_by_label(label)
        df.loc[:, TransactionLabeled.Amount] = df.loc[:, TransactionLabeled.Amount] * -1
        mean: float = self.monthly_costs.get_averaged_expenses_by_label().loc[label] * -1
        figure: go.Figure = create_line_plot_figure(df, mean, label, color, dark_mode_off)
        return figure

    def plot_sublabel_line_chart(
        self,
        transactions_by_label_pie_click_data: dict,
        transactions_by_label_pie: dict,
        transactions_by_sublabel_pie_click_data: dict,
        transactions_by_sublabel_pie: dict,
        dark_mode_off: bool,
        *_,
    ) -> go.Figure:
        label, _ = get_active_label_and_color(
            transactions_by_label_pie_click_data, transactions_by_label_pie
        )
        sublabel, color = get_active_sublabel_and_color(
            transactions_by_sublabel_pie_click_data, transactions_by_sublabel_pie
        )
        df: pd.DataFrame = self.monthly_costs.get_monthly_expenses_by_sublabel(label, sublabel)
        df.loc[:, TransactionLabeled.Amount] = df.loc[:, TransactionLabeled.Amount] * -1
        mean: float = self.monthly_costs.get_averaged_expenses_by_sublabel(label).loc[sublabel] * -1
        figure: go.Figure = create_line_plot_figure(df, mean, sublabel, color, dark_mode_off)
        return figure

    def plot_income_line_chart(
        self,
        income_pie_click_data: dict,
        income_pie: dict,
        dark_mode_off: bool,
        *_,
    ) -> go.Figure:
        label = 'Einkommen'
        sublabel, color = get_active_sublabel_and_color(income_pie_click_data, income_pie)
        df: pd.DataFrame = self.monthly_costs.get_monthly_expenses_by_sublabel(label, sublabel)
        mean: float = self.monthly_costs.get_averaged_income().loc[sublabel]
        figure: go.Figure = create_line_plot_figure(df, mean, sublabel, color, dark_mode_off)

        return figure

    def plot_expenses_bar(
        self,
        begin_dropdown_data: str,
        end_dropdown_data: str,
        dark_mode_off: bool,
        *_,
    ) -> go.Figure:
        self.monthly_costs.set_start_and_end_date(
            pd.to_datetime(begin_dropdown_data), pd.to_datetime(end_dropdown_data)
        )
        if self.monthly_costs.get_n_months_to_analyze() == 1:
            df: pd.DataFrame = self.monthly_costs.get_daily_expenses()
        else:
            df: pd.DataFrame = self.monthly_costs.get_monthly_expenses()
        figure: go.Figure = create_bar_plot_figure(df, dark_mode_off)
        return figure

    def run(self) -> None:
        self.app.run(debug=True)


def create_bar_plot_figure(df: pd.DataFrame, dark_mode_off: bool) -> go.Figure:
    figure: go.Figure = px.bar(
        data_frame=df,
        x=TransactionLabeled.Date,
        y=TransactionLabeled.Amount,
        color=TransactionLabeled.Amount,
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        template=extract_theme_from_mode(dark_mode_off),
    )
    return figure


def create_line_plot_figure(
    df: pd.DataFrame, mean: float, title: str, color: str, dark_mode_off: bool
) -> go.Figure:
    figure: go.Figure = px.line(
        data_frame=df,
        x=TransactionLabeled.Date,
        y=TransactionLabeled.Amount,
        title=title,
        markers=True,
        color_discrete_sequence=[color],
        template=extract_theme_from_mode(dark_mode_off),
    )
    figure.add_hline(mean, line_dash='dot', line_color=color, annotation_text=f'Mittel: {mean:.0f}')
    return figure


def create_pie_plot_figure(df: pd.DataFrame, names: str, dark_mode_off: bool) -> go.Figure:
    figure: go.Figure = px.pie(
        df,
        values=TransactionLabeled.Amount,
        names=names,
        template=extract_theme_from_mode(dark_mode_off),
    )
    return figure


def extract_theme_from_mode(dark_mode_off: bool) -> str:
    theme: str = 'bootstrap'
    if not dark_mode_off:
        theme += '_dark'
    return theme


def extract_date_from_click_data(
    monthly_transactions_plot_click_data: dict,
    month_split_day: int,
) -> pd.Timestamp:
    clicked_date = pd.to_datetime(monthly_transactions_plot_click_data['points'][0]['label'])
    value: pd.Timestamp = pd.Timestamp(
        year=clicked_date.year, month=clicked_date.month, day=month_split_day
    )  # type: ignore
    return value


def get_active_label_and_color(click_data: dict, figure_pie: dict) -> tuple[str, str]:
    label: str = figure_pie['data'][0]['labels'][0]
    color: str = figure_pie['layout']['template']['layout']['colorway'][0]
    if click_data:
        label: str = click_data['points'][0]['label']
        color = click_data['points'][0]['color']
    return label, color


def get_active_sublabel_and_color(click_data_sublabel: dict, figure_pie: dict) -> tuple[str, str]:
    all_sublabels: list[str] = figure_pie['data'][0]['labels']
    default_sublabel: str = all_sublabels[0]
    default_color: str = figure_pie['layout']['template']['layout']['colorway'][0]

    if click_data_sublabel:
        sublabel: str = click_data_sublabel['points'][0]['label']
        color: str = click_data_sublabel['points'][0]['color']
        if sublabel not in all_sublabels:
            sublabel: str = default_sublabel
            color: str = default_color
    else:
        sublabel: str = default_sublabel
        color: str = default_color
    return sublabel, color
