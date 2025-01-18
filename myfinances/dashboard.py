import plotly.express as px
from dash import Dash, dcc, html

from myfinances.monthly_costs import MonthlyCosts


class Dashboard:
    def __init__(self, monthly_costs: MonthlyCosts) -> None:
        self.app: Dash = Dash()
        self.monthly_costs: MonthlyCosts = monthly_costs
        self.app.layout = [
            html.Div(children='Finances Overview'),
            dcc.Graph(
                figure=px.line(
                    self.monthly_costs.get_monthly_expenses(),
                    x='Date',
                    y='Amount',
                )
            ),
            dcc.Graph(
                figure=px.pie(
                    self.monthly_costs.get_averaged_expenses_by_label()
                    .drop('Einkommen')
                    .mul(-1)
                    .reset_index(),
                    values='Amount',
                    names='Label',
                )
            ),
            html.Div(
                [
                    html.Label(
                        f'Available: {monthly_costs.get_averaged_expenses_by_label().sum()}'
                    ),
                ]
            ),
        ]

    def run(self) -> None:
        self.app.run(debug=True)
