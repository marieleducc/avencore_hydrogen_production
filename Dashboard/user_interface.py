"""User interface definition for the dashboard"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shiny import ui  # noqa: E402
from shinywidgets import output_widget

from Resolution.optimisation import (  # noqa: E402
    RES_MAX_CAPA_BAT,
    RES_MAX_PWR_BAT,
    RES_BENEF_ANNUAL
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
            ui.card(
                ui.card_header(
                    "Entries",
                    style="color:#FFFFFF; background:#0A1C63 !important;", 
                    #TODO : liste des paramètres qu'on peut modifer
                ), 
                ui.layout_column_wrap(
                    ui.input_numeric(
                    id="id_h2_price",
                    label="Price of green hydrogen",
                    value=10.0,
                    ),
                    ui.input_numeric(
                        id="id_electro_pwr",
                        label="Maximal power of the electrolyser (MW)",
                        value=100.0,
                    ),
                    ui.input_numeric(
                        id="id_electro_yield",
                        label="Global yield of the electrolyser",
                        value=1.0,
                        min=0.0,
                        max=1.0,
                    ),
                    ui.input_numeric(
                        id="id_electro_u_min",
                        label="Minimal fraction of charge",
                        value=0.0,
                        min=0.0,
                        max=1.0,
                    ),
                    ui.input_numeric(
                        id="id_electro_u_max",
                        label="Maximal fraction of charge",
                        value=0.95,
                        min=0.0,
                        max=1.0
                    ),
                    ui.input_numeric(
                        id="id_ramp_electro",
                        label="Maximal ramp electrolyser (MW/h)",
                        value=10.0,
                    ),
                    ui.input_numeric(
                        id="id_h2_target",
                        label="Annual hydrogen production target",
                        value=10_000_000.0,
                    ),
                    width=1/2,
                ),
                ui.input_action_button(
                    id="simulation",
                    label="Generate simulation",
                    class_="btn-action"
                ),  
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Optimal battery power",
                    f"{RES_MAX_PWR_BAT} MW", 
                    style="color:#0A1C63; background:#FFFFFF !important;", 
                    showcase=ui.img(src="battery.png", height="40px")  
                ),
                ui.value_box(
                    "Mean power electrolyser",
                    f"{RES_MAX_CAPA_BAT} MW", 
                    style="color:#0A1C63; background:#FFFFFF !important;", 
                    showcase=ui.img(src="electrolyser.png", height="40px")  
                ),
                ui.value_box(
                    "Total benefits",
                    f"{RES_BENEF_ANNUAL} €", 
                    style="color:#0A1C63; background:#FFFFFF !important;", 
                    showcase=ui.img(src="money.png", height="40px")  
                ),
                width=1/3,
            ), 
            output_widget(id="graph_soc_price_electro"),
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
