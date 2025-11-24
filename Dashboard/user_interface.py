"""User interface definition for the dashboard"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shiny import ui

from Resolution.optimisation import (
    RES_CAPEX_BAT_ENERGY,
    RES_CAPEX_BAT_POWER,
    RES_TOTAL_COST
    )


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
                        "Entries",
                        style="color:#0A1C63; background:#FFFFFF !important;", 
                        #TODO : liste des paramètres qu'on peut modifer
                    )
                ),
                ui.value_box(
                    "Optimal battery power",
                    f"{RES_CAPEX_BAT_POWER} MW", 
                    style="color:#0A1C63; background:#FFFFFF !important;", 
                    showcase=ui.img(src="battery.png", height="40px")  
                ),
                ui.value_box(
                    "Mean power electrolyser",
                    f"{RES_CAPEX_BAT_ENERGY} MW", 
                    style="color:#0A1C63; background:#FFFFFF !important;", 
                    showcase=ui.img(src="electrolyser.png", height="40px")  
                ),
                ui.value_box(
                    "Total costs",
                    f"{RES_TOTAL_COST} €", 
                    style="color:#0A1C63; background:#FFFFFF !important;", 
                    showcase=ui.img(src="money.png", height="40px")  
                ),
                width=1/4,
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
