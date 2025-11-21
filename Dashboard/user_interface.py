"""User interface definition for the dashboard"""

from pathlib import Path
from shiny import ui

def ui_function() -> ui.Tag:
    return ui.page_fluid(
        ui.head_content(
            ui.include_css(Path(__file__).parent / "www" / "styles.css")
        ),

        ui.div(
            ui.layout_columns(
                ui.tags.img(src="avencore_logo.jpg", width="190", height="30"),
                col_widths=(1, 11),
            ),
            style="background-color:#FFFFFF; padding:10px; display:flex; align-items:center;"
        ),

        ui.div(
            ui.layout_column_wrap(
                ui.card(
                    ui.card_header(
                        "Jsp quoi encore",
                        style="color:#0A1C63; background:#FFFFFF !important;"
                    )
                ),
                ui.card(
                    ui.card_header(
                        "Jsp quoi encore 2",
                        style="color:#0A1C63; background:#FFFFFF !important;"
                    )
                ),
                width=1/2,
            ), 
            style="padding: 2em;"
        ),

        ui.div(
            ui.tags.style(
                """
                h4 {
                    margin-top: 3em;
                }
                """
            ),
            style="width:80%; margin: 0 auto;",
            class_="app-footer"
        ),
        class_="container-fluid",
        id="app-root"
    )
