"""App definition for the dashboard"""

"""Shiny App"""

from pathlib import Path

from shiny import App, ui

from user_interface import ui_function
from server import server


# Create User Interface
app_ui: ui.Tag = ui_function()

# Create shiny app using both front-end and back-end
www_dir = Path(__file__).parent / "www"
app: App = App(app_ui, server, static_assets=www_dir)