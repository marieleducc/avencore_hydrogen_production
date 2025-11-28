"""Server definition for the dashboard"""

import plotly.graph_objects as go

from shiny import Inputs, Outputs, reactive, render, ui
from shinywidgets import render_widget
from plots import plot_average_daily_profile
from Resolution.optimisation import df
    
def server(input_shiny: Inputs, output_shiny: Outputs, session) -> None:
    @output_shiny
    @render_widget
    def graph_soc_price_electro():
        return plot_average_daily_profile(df)

