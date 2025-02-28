import plotly.express as px
from dash import Dash, dcc, dependencies, html

from myfinances.monthly_costs import MonthlyCosts


class Dashboard:
    def __init__(self, monthly_costs: MonthlyCosts) -> None:
        self.app: Dash = Dash()
        self.monthly_costs: MonthlyCosts = monthly_costs
        self.app.layout = [
            html.Div(children='Finances Overview'),
            dcc.Graph(
                figure=px.bar(
                    self.monthly_costs.get_monthly_expenses(),
                    x='Date',
                    y='Amount',
                    color='Amount',
                    color_continuous_scale='RdYlGn',
                    color_continuous_midpoint=0,
                )
            ),
            dcc.Graph(
                id='label_pie',
                figure=px.pie(
                    self.monthly_costs.get_averaged_expenses_by_label()
                    .drop('Einkommen')
                    .mul(-1)
                    .reset_index(),
                    values='Amount',
                    names='Label',
                ),
            ),
            dcc.Graph(
                id='sublabel_pie',
            ),
            html.Div(
                [
                    html.Label(
                        f'Available: {monthly_costs.get_averaged_expenses_by_label().sum()}'
                    ),
                ]
            ),
            dcc.Graph(
                id='income_pie',
                figure=px.pie(
                    self.monthly_costs.get_averaged_income(),
                    values='Amount',
                    names='Sublabel',
                ),
            ),
        ]
        (  # type: ignore
            self.app.callback(
                dependencies.Output('sublabel_pie', 'figure'),
                dependencies.Input('label_pie', 'clickData'),
            )(self.create_sublabel_pie),
        )

    def create_sublabel_pie(self, clickData):  # noqa: N803
        label = 'Sonstiges'
        if clickData:
            label: str = clickData['points'][0]['label']
        figure = px.pie(
            self.monthly_costs.get_averaged_expenses_by_sublabel(label).mul(-1).reset_index(),
            values='Amount',
            names='Sublabel',
        )
        return figure

    def run(self) -> None:
        self.app.run(debug=True)
