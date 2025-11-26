"""User interface definition for the dashboard"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Resolution.optimisation import optimisation_function


# Initialisation de l'app Dash
app = dash.Dash(__name__)

# Layout du dashboard
app.layout = html.Div([
    html.H1("Optimisation Batterie - Production H2", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
    
    # Section des inputs
    html.Div([
        html.Div([
            html.Label("Technologie d'électrolyseur", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='techno-dropdown',
                options=[
                    {'label': 'AEL (Alkaline)', 'value': 'AEL'},
                    {'label': 'PEM (Proton Exchange Membrane)', 'value': 'PEM'},
                    {'label': 'SOEC (Solid Oxide)', 'value': 'SOEC'}
                ],
                value='PEM',
                clearable=False
            )
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
        
        html.Div([
            html.Label("Prix du H2 (€/kg)", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='prix-h2',
                type='number',
                value=5.0,
                min=0,
                step=0.1,
                style={'width': '100%'}
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'marginBottom': 20}),
    
    html.Div([
        html.Div([
            html.Label("Puissance de l'électrolyseur (MW)", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='puissance-electrolyser',
                type='number',
                value=100.0,
                min=10.0,
                step=10.0,
                style={'width': '100%'}
            )
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
        
        html.Div([
            html.Label("Nombre d'années du projet", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='nb-annees',
                type='number',
                value=20,
                min=1,
                max=50,
                step=1,
                style={'width': '100%'}
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'marginBottom': 20}),
    
    html.Div([
        html.Div([
            html.Label("Objectif de production annuelle H2 (tonnes)", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='objectif-production',
                type='number',
                value=10000,
                min=0,
                step=500,
                style={'width': '100%'}
            )
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
        
        html.Div([
            html.Label("Revente d'électricité possible ?", style={'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='revente-elec',
                options=[
                    {'label': 'OUI', 'value': 'YES'},
                    {'label': 'NON', 'value': 'NO'}
                ],
                value='YES',
                inline=True,
                style={'marginTop': 8}
            )
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'marginBottom': 30}),
    
    # Bouton de calcul
    html.Div([
        html.Button('Lancer l\'optimisation', 
                    id='run-button', 
                    n_clicks=0,
                    style={
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'padding': '12px 30px',
                        'fontSize': '16px',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer'
                    })
    ], style={'textAlign': 'center', 'marginBottom': 40}),
    
    # Section des résultats
    html.Div(id='results-container', children=[
        # KPIs
        html.Div(id='kpi-section', style={'marginBottom': 30}),
        
        # Graphiques
        html.Div([
            dcc.Graph(id='graph-journee-moyenne'),
        ], style={'marginBottom': 30}),
        
        html.Div([
            dcc.Graph(id='graph-puissance-vs-prix'),
        ])
    ])
    
], style={'padding': '40px', 'maxWidth': '1400px', 'margin': '0 auto', 'fontFamily': 'Arial, sans-serif'})


# Callback pour l'optimisation
@app.callback(
    [Output('kpi-section', 'children'),
     Output('graph-journee-moyenne', 'figure'),
     Output('graph-puissance-vs-prix', 'figure')],
    [Input('run-button', 'n_clicks')],
    [State('techno-dropdown', 'value'),
     State('prix-h2', 'value'),
     State('puissance-electrolyser', 'value'),
     State('nb-annees', 'value'),
     State('objectif-production', 'value'),
     State('revente-elec', 'value')]
)
def run_optimization(n_clicks, techno, prix_h2, puissance_elec, nb_annees, objectif_prod, revente_elec):
    if n_clicks == 0:
        # Retourner des graphiques vides au démarrage
        empty_fig1 = go.Figure()
        empty_fig1.update_layout(title="Journée moyenne - Lancez l'optimisation")
        empty_fig2 = go.Figure()
        empty_fig2.update_layout(title="Puissance vs Prix spot - Lancez l'optimisation")
        return html.Div(), empty_fig1, empty_fig2
    
    output_dic, df = optimisation_function(
         techno, prix_h2, puissance_elec, nb_annees, objectif_prod, revente_elec
    )
     
    # KPIs
    kpi_content = html.Div([
        html.H2("Résultats de l'optimisation", style={'color': '#2c3e50', 'marginBottom': 20}),
        html.Div([
            html.Div([
                html.H3("Batterie installée", style={'color': '#34495e'}),
                html.P(f"Puissance : {output_dic['MAX_PWR_BAT']:.2f} MW", style={'fontSize': '18px', 'margin': '5px 0'}),
                html.P(f"Capacité : {output_dic['MAX_CAPA_BAT']:.2f} MWh", style={'fontSize': '18px', 'margin': '5px 0'}),
            ], style={
                'width': '48%', 
                'display': 'inline-block', 
                'padding': '20px',
                'backgroundColor': '#ecf0f1',
                'borderRadius': '10px',
                'marginRight': '4%'
            }),
            
            html.Div([
                html.H3("Performance économique", style={'color': '#34495e'}),
                html.P(f"Production H2 annuelle : {output_dic['H2_TOTAL'] / 1000:.2f} tonnes", 
                       style={'fontSize': '18px', 'margin': '5px 0'}),
                html.P(f"Chiffre d'affaires total : {output_dic['CA_TOTAL'] / 1e6:.2f} M€", 
                       style={'fontSize': '18px', 'margin': '5px 0', 'fontWeight': 'bold', 'color': '#27ae60'}),
            ], style={
                'width': '48%', 
                'display': 'inline-block',
                'padding': '20px',
                'backgroundColor': '#ecf0f1',
                'borderRadius': '10px'
            }),
        ])
    ])
    
    # Graphique 1 : Journée moyenne
    df_daily_avg = df.groupby(df['Date'].dt.hour).mean()
    
    fig1 = go.Figure()
    
    # Prix spot sur axe secondaire
    fig1.add_trace(go.Scatter(
        x=df_daily_avg.index,
        y=df_daily_avg['Spot_Price'],
        name='Prix spot',
        yaxis='y2',
        line=dict(color='#e74c3c', width=2)
    ))
    
    fig1.add_trace(go.Scatter(
        x=df_daily_avg.index,
        y=df_daily_avg['P_ch'],
        name='Puissance charge',
        line=dict(color='#3498db', width=2)
    ))
    
    fig1.add_trace(go.Scatter(
        x=df_daily_avg.index,
        y=df_daily_avg['P_dis'],
        name='Puissance décharge',
        line=dict(color='#f39c12', width=2)
    ))
    
    fig1.add_trace(go.Scatter(
        x=df_daily_avg.index,
        y=df_daily_avg['P_electro'],
        name='Puissance électrolyseur',
        line=dict(color='#2ecc71', width=2)
    ))
    
    fig1.update_layout(
        title='Journée moyenne - Profils de puissance et prix',
        xaxis=dict(title='Heure de la journée'),
        yaxis=dict(title='Puissance (MW)', side='left'),
        yaxis2=dict(title='Prix spot (€/MWh)', side='right', overlaying='y'),
        hovermode='x unified',
        legend=dict(x=0, y=1.15, orientation='h'),
        height=500
    )
    
    # Graphique 2 : Puissance vs Prix spot
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=df['Spot_Price'],
        y=df['P_ch'],
        mode='markers',
        name='Charge',
        marker=dict(color='#3498db', size=4, opacity=0.5)
    ))
    
    fig2.add_trace(go.Scatter(
        x=df['Spot_price'],
        y=df['P_dis'],
        mode='markers',
        name='Décharge',
        marker=dict(color='#f39c12', size=4, opacity=0.5)
    ))
    
    fig2.update_layout(
        title='Stratégie de charge/décharge en fonction du prix spot',
        xaxis=dict(title='Prix spot (€/MWh)'),
        yaxis=dict(title='Puissance (MW)'),
        hovermode='closest',
        legend=dict(x=0, y=1.1, orientation='h'),
        height=500
    )
    
    return kpi_content, fig1, fig2


# Lancer l'application
if __name__ == '__main__':
    app.run(debug=True, port=8050)