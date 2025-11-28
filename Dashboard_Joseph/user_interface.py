import dash
from dash import dcc, html, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import sys, os

# Simulation de l'import pour que le code soit runnable si vous n'avez pas le fichier
# Remplacez ceci par votre import réel : 
# from Resolution.optimisation import optimisation_function
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from Resolution.optimisation import optimisation_function
except ImportError:
    # Fonction Mock pour tester si le fichier n'existe pas
    import time
    def optimisation_function(techno, prix, puissance, annees, obj, revente):
        time.sleep(1.5) # Simulation du temps de calcul
        dates = pd.date_range(start='2024-01-01', periods=24*365, freq='h')
        df = pd.DataFrame({
            'Date': dates,
            'Spot_Price': np.random.uniform(50, 150, len(dates)),
            'P_ch': np.random.uniform(0, 10, len(dates)),
            'P_dis': np.random.uniform(0, 10, len(dates)),
            'P_electro': np.random.uniform(20, 80, len(dates))
        })
        
        # Mock du nouveau dictionnaire de sortie
        dic = {
            # === ⚙️ PARAMÈTRES D'ENTRÉES ===
            "H2_PRICE": 7.0,
            "CAPEX_BAT_POWER": 100000,
            "CAPEX_BAT_ENERGY": 150000,
            "PROJECT_LIFETIME": 20,
            "DISCOUNT_RATE": 0.05,
            # === ⚙️ PARAMÈTRES TECHNIQUES ===
            "MAX_PWR_BAT": 50.5,
            "MAX_CAPA_BAT": 200.0,
            "MAX_PWR_ELECTRO": 100.0,
            # === 🔧 PERFORMANCE ÉLECTROLYSEUR ===
            "MEAN_PWR_ELECTRO": 85.0,
            "TOTAL_ENE_ELECTRO": 750000,
            "EFFECTIVE_TIME": 8500, # heures
            "EFFECTIVE_POWER": 0.95, # %
            # === 🌱 HYDROGÈNE & CARBONE ===
            "H2_TOTAL": 5000000,
            "CO2_TOTAL": 120000,
            "CO2_INTENSITY": 2.5,
            "H2_COST": 4.5,
            # === 💶 ÉCONOMIE ===
            "CA_TOTAL": 35000000,
            "CAPEX_COST": 5000000,
            "ELEC_COST": 10000000,
            "ELEC_COST_MEAN": 55.0,
            "TOTAL_COST": 20000000,
            "BENEF_ANNUAL": 1500000,
        }
        return dic, df

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# --------------------------
#       GLOBAL STYLE
# --------------------------
CARD_STYLE = {
    "backgroundColor": "white",
    "borderRadius": "12px",
    "padding": "20px",
    "boxShadow": "0 4px 10px rgba(0,0,0,0.1)",
    "marginBottom": "25px"
}

LABEL_STYLE = {"fontWeight": "bold", "display": "flex", "alignItems": "center"}
ICON_STYLE = {"height": "22px", "marginRight": "8px"}

# Style pour les blocs de KPI
KPI_BOX_STYLE = {
    "backgroundColor": "#f8f9fa",
    "borderRadius": "8px",
    "padding": "15px",
    "margin": "10px",
    "flex": "1",
    "minWidth": "200px",
    "textAlign": "center",
    "boxShadow": "inset 0 0 5px rgba(0,0,0,0.05)"
}

KPI_TITLE_STYLE = {"color": "#6c757d", "fontSize": "14px", "marginBottom": "5px", "textTransform": "uppercase", "letterSpacing": "1px"}
KPI_VALUE_STYLE = {"color": "#1f2a44", "fontSize": "22px", "fontWeight": "bold"}
KPI_SUB_STYLE = {"color": "#adb5bd", "fontSize": "12px", "marginTop": "5px"}

# --------------------------
#          LAYOUT
# --------------------------
app.layout = html.Div([

    # LOGO TOP-RIGHT
    html.Div([
        html.Img(src="/assets/avencore_logo.jpg", alt="Logo",
                 style={"height": "70px", "float": "right"})
    ]),

    html.H1("Optimisation Batterie – Production H₂",
            style={"textAlign": "center", "color": "#1f2a44", 
                   "marginBottom": 20, "marginTop": -20, "fontWeight": "bold"}),

    # --- INPUT PANEL ---
    html.Div([
        html.H2("Paramètres d'entrée", style={"color": "#1f2a44"}),

        # Row 1
        html.Div([
            html.Div([
                html.Label([
                    html.Img(src="/assets/electrolyser.png", style=ICON_STYLE, alt=""),
                    "Technologie d'électrolyseur"
                ], style=LABEL_STYLE),
                dcc.Dropdown(
                    id='techno-dropdown',
                    options=[
                        {"label": "AEL (Alkaline)", "value": "AEL"},
                        {"label": "PEM", "value": "PEM"},
                        {"label": "SOEC", "value": "SOEC"},
                    ],
                    value="PEM",
                    clearable=False
                )
            ], style={"width": "48%", "display": "inline-block", "marginRight": "4%"}),

            html.Div([
                html.Label([
                    html.Img(src="/assets/hydrogen.jpg", style=ICON_STYLE, alt=""),
                    "Prix du H₂ (€/kg)"
                ], style=LABEL_STYLE),
                dcc.Input(id="prix-h2", type="number", value=7.0,
                          min=0, step=0.1, style={"width": "100%"})
            ], style={"width": "48%", "display": "inline-block"}),
        ], style={"marginBottom": 15}),

        # Row 2
        html.Div([
            html.Div([
                html.Label([
                    html.Img(src="/assets/battery.png", style=ICON_STYLE, alt=""),
                    "Puissance électrolyseur (MW)"
                ], style=LABEL_STYLE),
                dcc.Input(id="puissance-electrolyser", type="number",
                          value=100.0, min=10, step=10, style={"width": "100%"})
            ], style={"width": "48%", "display": "inline-block", "marginRight": "4%"}),

            html.Div([
                html.Label([
                    html.Img(src="/assets/calendar.png", style=ICON_STYLE, alt=""),
                    "Durée projet (années)"
                ], style=LABEL_STYLE),
                dcc.Input(id="nb-annees", type="number",
                          value=20, min=1, max=50, style={"width": "100%"})
            ], style={"width": "48%", "display": "inline-block"}),
        ], style={"marginBottom": 15}),

        # Row 3
        html.Div([
            html.Div([
                html.Label([
                    html.Img(src="/assets/target.png", style=ICON_STYLE, alt=""),
                    "Objectif production annuelle (kg)"
                ], style=LABEL_STYLE),
                dcc.Input(id="objectif-production", type="number",
                          value=10_000_000, min=0, step=1000000, style={"width": "100%"})
            ], style={"width": "48%", "display": "inline-block", "marginRight": "4%"}),

            html.Div([
                html.Label([
                    "Revente électricité ?"
                ], style=LABEL_STYLE),
                dcc.RadioItems(
                    id="revente-elec",
                    options=[{"label": "Oui", "value": "YES"},
                             {"label": "Non", "value": "NO"}],
                    value="NO",
                    inline=True
                )
            ], style={"width": "48%", "display": "inline-block"}),
        ], style={"marginBottom": 20}),

        # BUTTON
        html.Div([
            html.Button(
                "Lancer l'optimisation",
                id="run-button",
                n_clicks=0,
                style={
                    "backgroundColor": "#1f77b4",
                    "color": "white",
                    "padding": "14px 34px",
                    "fontSize": "18px",
                    "border": "none",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "fontWeight": "bold",
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                }
            )
        ], style={"textAlign": "center", "marginBottom": 30})
    ], style=CARD_STYLE),

    # --- RESULTS ---
    dcc.Loading(
        id="loading-spinner",
        type="circle",
        color="#1f77b4",
        children=html.Div(id="results-container", children=[
            # Zone KPI
            html.Div(id="kpi-section"),
            # Graphique seul
            html.Div([dcc.Graph(id="graph-journee-moyenne")], style={**CARD_STYLE, "display": "none"}, id="container-graph-1"),
        ])
    )

], style={"padding": "40px", "maxWidth": "1400px", "margin": "0 auto",
          "backgroundColor": "#f5f7fb", "fontFamily": "Arial, sans-serif"})


# -----------------------------------------
# HELPER POUR AFFICHER UNE KPI
# -----------------------------------------
def create_kpi_card(title, value, unit="", subtext=""):
    return html.Div([
        html.Div(title, style=KPI_TITLE_STYLE),
        html.Div(f"{value} {unit}", style=KPI_VALUE_STYLE),
        html.Div(subtext, style=KPI_SUB_STYLE) if subtext else None
    ], style=KPI_BOX_STYLE)

# -----------------------------------------
# OPTIMISATION CALLBACK
# -----------------------------------------
@app.callback(
    [Output('kpi-section', 'children'),
     Output('graph-journee-moyenne', 'figure'),
     Output('container-graph-1', 'style')],
    Input('run-button', 'n_clicks'),
    [State('techno-dropdown', 'value'),
     State('prix-h2', 'value'),
     State('puissance-electrolyser', 'value'),
     State('nb-annees', 'value'),
     State('objectif-production', 'value'),
     State('revente-elec', 'value')],
    prevent_initial_call=True
)
def run_optimization(n_clicks, techno, prix_h2, puissance_elec, nb_annees, objectif_prod, revente_elec):

    if not n_clicks:
        raise PreventUpdate

    # -------------------------
    # RUN OPTIMISATION
    # -------------------------
    output_dic, df = optimisation_function(
        techno, prix_h2, puissance_elec, nb_annees, objectif_prod, revente_elec
    )

    # -------------------------
    # 1. BUILD GRAPH (Moyenne Journalière)
    # -------------------------
    if 'Date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Date']):
        df_daily_avg = df.groupby(df['Date'].dt.hour).mean()
        x_axis = df_daily_avg.index
    else:
        df_daily_avg = df.mean()
        x_axis = range(24)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_axis, y=df_daily_avg.get('Spot_Price', []),
                              name="Prix spot", yaxis="y2", line=dict(color='gray', dash='dot')))
    fig1.add_trace(go.Scatter(x=x_axis, y=df_daily_avg.get('P_ch', []), name="Charge Batterie", fill='tozeroy'))
    fig1.add_trace(go.Scatter(x=x_axis, y=df_daily_avg.get('P_dis', []), name="Décharge Batterie", fill='tozeroy'))
    fig1.add_trace(go.Scatter(x=x_axis, y=df_daily_avg.get('P_electro', []), name="Electrolyseur"))
    
    fig1.update_layout(
        title="Profil Horaire Moyen",
        yaxis2=dict(overlaying="y", side="right", title="Prix (€/MWh)"),
        yaxis=dict(title="Puissance (MW)"),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=40, r=40, t=60, b=40),
        template="plotly_white"
    )

    # -------------------------
    # 2. BUILD KPI SECTION
    # -------------------------
    
    # --- Bloc 1: Technique ---
    tech_section = html.Div([
        html.H3("⚙️ Dimensionnement", style={"fontSize": "16px", "color": "#1f77b4", "marginBottom": "10px"}),
        html.Div([
            create_kpi_card("Batterie Puissance", f"{output_dic.get('MAX_PWR_BAT', 0):.1f}", "MW"),
            create_kpi_card("Batterie Capacité", f"{output_dic.get('MAX_CAPA_BAT', 0):.1f}", "MWh"),
            create_kpi_card("Electrolyseur", f"{output_dic.get('MAX_PWR_ELECTRO', 0):.0f}", "MW"),
        ], style={"display": "flex", "flexWrap": "wrap"})
    ], style={"marginBottom": "20px"})

    # --- Bloc 2: Performance H2 ---
    perf_section = html.Div([
        html.H3("🏭 Production H₂ & Usage", style={"fontSize": "16px", "color": "#2ca02c", "marginBottom": "10px"}),
        html.Div([
            create_kpi_card("Production H₂ Totale", f"{output_dic.get('H2_TOTAL', 0)/1000:,.0f}", "t"),
            create_kpi_card("Nombre d'heures en Fonctionnement", f"{output_dic.get('EFFECTIVE_TIME', 0):,.0f}", "h"),
            create_kpi_card("Facteur de Charge", f"{output_dic.get('EFFECTIVE_POWER', 0):.1f}", "%"),
        ], style={"display": "flex", "flexWrap": "wrap"})
    ], style={"marginBottom": "20px"})

    # --- Bloc 3: Environnement ---
    env_section = html.Div([
        html.H3("🌱 Impact Environnemental", style={"fontSize": "16px", "color": "#1f2a44", "marginBottom": "10px"}),
        html.Div([
            create_kpi_card("CO₂ Total Émis", f"{output_dic.get('CO2_TOTAL', 0)/1000:,.0f}", "tCO₂"),
            create_kpi_card("Intensité Carbone", f"{output_dic.get('CO2_INTENSITY', 0):.2f}", "kgCO₂/kgH₂"),
        ], style={"display": "flex", "flexWrap": "wrap"})
    ], style={"marginBottom": "20px"})

    # --- Bloc 4: Économie ---
    eco_section = html.Div([
        html.H3("💶 Bilan Économique", style={"fontSize": "16px", "color": "#ff7f0e", "marginBottom": "10px"}),
        html.Div([
            create_kpi_card("CA Total", f"{output_dic.get('CA_TOTAL', 0)/1e6:.1f}", "M€"),
            create_kpi_card("Coût Complet (LCOH)", f"{output_dic.get('H2_COST', 0):.2f}", "€/kg"),
            create_kpi_card("Bénéfice Annuel", f"{output_dic.get('BENEF_ANNUAL', 0)/1e6:.2f}", "M€/an"),
        ], style={"display": "flex", "flexWrap": "wrap"}),
         html.Div([
            create_kpi_card("CAPEX Total", f"{output_dic.get('CAPEX_COST', 0)/1e6:.1f}", "M€"),
            create_kpi_card("Coût Élec. Moyen", f"{output_dic.get('ELEC_COST_MEAN', 0):.1f}", "€/MWh"),
        ], style={"display": "flex", "flexWrap": "wrap"})
    ])

    # Assemblage final
    kpi_content = html.Div([
        html.H2("Résultats de l'optimisation", style={"color": "#1f2a44", "marginTop": 0}),
        html.Hr(style={"borderTop": "1px solid #eee"}),
        html.Div([
            # Colonne Gauche
            html.Div([tech_section, env_section], style={"width": "48%", "verticalAlign": "top", "display": "inline-block"}),
            # Colonne Droite (spacer de 4%)
            html.Div(style={"width": "4%", "display": "inline-block"}),
            html.Div([perf_section, eco_section], style={"width": "48%", "verticalAlign": "top", "display": "inline-block"}),
        ])
    ], style=CARD_STYLE)

    visible_style = CARD_STYLE.copy()
    visible_style['display'] = 'block'

    return kpi_content, fig1, visible_style


# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    app.run(debug=True, port=8050)