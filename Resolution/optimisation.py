"""File for the definition of the model"""
import sys
from pathlib import Path    

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("PROJECT_ROOT =", PROJECT_ROOT)

# Libraries imports
import pyomo.environ as pyo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Custom imports
from Resolution.constants import *
from Resolution.loading import *
from Resolution.battery_simulation import *
from Resolution.electrolyser_simulation import *
from Resolution.cost_functions import *

# ---- INPUT PARAMETERS ----

techno = "PEM"             # Electrolyser technology: "AEL", "PEM", "SOEC"
prix_H2 = 10               # Price of green H2 in €/kg
P_electro_max = 100        # Electrolyser power in MW
N = 20                     # Project lifetime (years)
H2_target = 8_000_000     # Annual H2 production target (kg)
Revente = "YES"            # "YES" if electricity resale is possible, "NO" otherwise

def optimisation_function(techno,prix_H2,P_electro_max,N,H2_target,Revente):
    
    constant_dic = modelConstants(techno,prix_H2,P_electro_max,N,H2_target,Revente)
    for key, value in constant_dic.items():
        globals()[key] = value
        
    model = pyo.ConcreteModel(techno,prix_H2,P_electro_max,N,H2_target,Revente)

    # ---- Sets ----
    model.T = pyo.RangeSet(0, T-1)   # on utilise 0..T-1 pour faciliter les indices
    # Pour les contraintes de rampe, on utilisera 1..T-1

    # ---- Limitation Variables ----
    model.P_bat_max = pyo.Var(domain=pyo.NonNegativeReals)  # Puissance installée batterie MW
    model.E_bat_max = pyo.Var(domain=pyo.NonNegativeReals)  # Capacité énergétique de la batterie MWh
    # model.phi = pyo.Var(domain=pyo.UnitInterval)            # fraction de la puissance de l'électrolyseur acheté sur le forward


    # ---- Operational Variables ----
    if Revente == "YES":
        model.P_spot = pyo.Var(model.T, domain=pyo.Reals)                  # Achat / Revente Autoriser
    else:   
        model.P_spot = pyo.Var(model.T, domain=pyo.NonNegativeReals)       # Puissance tirée au prix spot (Achat Uniquement)

    model.P_ch   = pyo.Var(model.T, domain=pyo.NonNegativeReals)       # Puissance de charge de la batterie
    model.P_dis  = pyo.Var(model.T, domain=pyo.NonNegativeReals)       # Puissance de décharge de la batterie
    model.P_electro   = pyo.Var(model.T, domain=pyo.NonNegativeReals)  # Puissance de l'électrolyseur
    model.SOC = pyo.Var(model.T, domain=pyo.NonNegativeReals)          # État de charge de la batterie en MWh
    model.H2 = pyo.Var(model.T, domain=pyo.NonNegativeReals)           # production de H2 (kg)

    # ---- Constraints ----
    model.PowerBalance = pyo.Constraint(model.T, rule=power_balance_rule)     # Power Balance
    model.SOCdyn = pyo.Constraint(model.T, rule=soc_dyn_rule)                 # Dynamics of battery state of charge
    model.SOCLowerBound = pyo.Constraint(model.T, rule=soc_lower_bound_rule)  # Lower Bound of battery SOC
    model.SOCUpperBound = pyo.Constraint(model.T, rule=soc_upper_bound_rule)  # Upper Bound of battery SOC
    model.PchLimit = pyo.Constraint(model.T, rule=p_ch_limit_rule)            # Charge Power Limit
    model.PdisLimit = pyo.Constraint(model.T, rule=p_dis_limit_rule)          # Discharge Power Limit
    model.PbatMax = pyo.Constraint(rule=p_bat_max)                            # Battery Power Installed Limit
    model.EbatMax = pyo.Constraint(rule=e_bat_max)                            # Battery Energy Installed Limit
    model.ElMin = pyo.Constraint(model.T, rule=el_min_rule)                   # Electrolyser Minimum Power
    model.ElMax = pyo.Constraint(model.T, rule=el_max_rule)                   # Electrolyser Maximum Power
    model.ElRamp = pyo.Constraint(model.T, rule=el_ramp_rule)                 # Electrolyser Ramp Constraint
    model.H2Production = pyo.Constraint(model.T, rule=h2_production_rule)     # H2 Production Relation
    model.H2Target = pyo.Constraint(rule=h2_target_rule)                      # H2 Annual Target
    model.Obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)        # Objective Function : minimize capex and energy costs


    # ---- Model Resolution ----
    solver = pyo.SolverFactory("highs")

    result = solver.solve(model, tee=True)

    print(result.solver.status, result.solver.termination_condition)


    # ---- Output ----  
    # Convert outputs to pandas Series for easier handling
    P_spot_series     = pd.Series({t: pyo.value(model.P_spot[t])     for t in model.T})
    P_ch_series       = pd.Series({t: pyo.value(model.P_ch[t])       for t in model.T})
    P_dis_series      = pd.Series({t: pyo.value(model.P_dis[t])      for t in model.T})
    P_electro_series  = pd.Series({t: pyo.value(model.P_electro[t])  for t in model.T})
    SOC_series        = pd.Series({t: pyo.value(model.SOC[t])        for t in model.T})
    H2_series         = pd.Series({t: pyo.value(model.H2[t])         for t in model.T})

    # Add to a DataFrame for easier analysis
    df["P_spot"] = P_spot_series
    df["P_ch"] = P_ch_series
    df["P_dis"] = P_dis_series
    df["P_electro"] = P_electro_series
    df["SOC"] = SOC_series
    df["H2"] = H2_series
    df["CO2_emissions"] = df["CO2_Intensity"] * df["P_spot"]

    # === 📥 PARAMÈTRES D'ENTRÉE ===
    MAX_PWR_ELECTRO      = P_electro_max
    H2_PRICE             = prix_H2
    CAPEX_BAT_POWER      = c_bat_P
    CAPEX_BAT_ENERGY     = c_bat_E
    PROJECT_LIFETIME     = N
    DISCOUNT_RATE        = r * 100

    # === ⚙️ PARAMÈTRES TECHNIQUES ===
    MAX_PWR_BAT          = pyo.value(model.P_bat_max)
    MAX_CAPA_BAT         = pyo.value(model.E_bat_max)


    # === 🔧 PERFORMANCE ÉLECTROLYSEUR ===
    MEAN_PWR_ELECTRO     = sum(pyo.value(model.P_electro[t]) for t in model.T) / len(model.T)
    TOTAL_ENE_ELECTRO    = sum(pyo.value(model.P_electro[t]) for t in model.T) * dt
    ELEC_COST_MEAN       = sum(price_elec[t] * pyo.value(model.P_spot[t]) * dt for t in model.T) / TOTAL_ENE_ELECTRO
    EFFECTIVE_TIME       = TOTAL_ENE_ELECTRO / (MAX_PWR_ELECTRO * 8760) * 100  # en %
    EFFECTIVE_POWER      = MEAN_PWR_ELECTRO / MAX_PWR_ELECTRO * 100  # en %

    # === 🌱 HYDROGÈNE & CARBONE ===
    H2_TOTAL             = sum(pyo.value(model.H2[t]) for t in model.T)
    CO2_TOTAL            = pyo.value(emissions_co2(model))
    CO2_INTENSITY        = CO2_TOTAL / H2_TOTAL



    # === 💶 ÉCONOMIE ===

    CA_TOTAL             = H2_TOTAL * prix_H2 - sum(price_elec[t] * min(0, pyo.value(model.P_spot[t])) * dt for t in model.T)
    CAPEX_COST           = pyo.value(capex_annual(model)) + c_electro * P_electro_max * alpha
    ELEC_COST            = sum(price_elec[t] * max(0, pyo.value(model.P_spot[t])) * dt for t in model.T)
    TOTAL_COST           = CAPEX_COST + ELEC_COST
    BENEF_ANNUAL         = CA_TOTAL - TOTAL_COST
    H2_COST              = TOTAL_COST / H2_TOTAL


    output_dic = {
        # === ⚙️ PARAMÈTRES TECHNIQUES ===
        "MAX_PWR_BAT": MAX_PWR_BAT,
        "MAX_CAPA_BAT": MAX_CAPA_BAT,
        "MAX_PWR_ELECTRO": MAX_PWR_ELECTRO,
        # === 🔧 PERFORMANCE ÉLECTROLYSEUR ===
        "MEAN_PWR_ELECTRO": MEAN_PWR_ELECTRO,
        "TOTAL_ENE_ELECTRO": TOTAL_ENE_ELECTRO,
        "EFFECTIVE_TIME": EFFECTIVE_TIME,
        "EFFECTIVE_POWER": EFFECTIVE_POWER,
        # === 🌱 HYDROGÈNE & CARBONE ===
        "H2_TOTAL": H2_TOTAL,
        "CO2_TOTAL": CO2_TOTAL,
        "CO2_INTENSITY": CO2_INTENSITY,
        "H2_COST": H2_COST,
        # === 💶 ÉCONOMIE ===
        "CA_TOTAL": CA_TOTAL,
        "CAPEX_COST": CAPEX_COST,
        "ELEC_COST": ELEC_COST,
        "ELEC_COST_MEAN": ELEC_COST_MEAN,
        "TOTAL_COST": TOTAL_COST,
        "BENEF_ANNUAL": BENEF_ANNUAL,
    }
    
    return output_dic, df

def fmt(x):
    """Format compact pour grands nombres : 1.2M, 7.5k, 9.3B ou 123.45."""
    if abs(x) >= 1e9:
        return f"{round(x)/1e9:.0f} B"
    elif abs(x) >= 1e6:
        return f"{round(x)/1e6:.0f} M"
    elif abs(x) >= 1e3:
        return f"{round(x)/1e3:.0f} k"
    elif abs(x) >= 1e2:
        return f"{round(x):.0f}"
    elif abs(x) >= 1e1:
        return f"{round(x):.0f}"
    else:
        return f"{x:.2f}"


print("\n===  📥 PARAMÈTRES D'ENTRÉE ===")
print("Puissance électrolyseur max (MW)     :", fmt(MAX_PWR_ELECTRO))
print("Prix du kg de H2 (€)                 :", fmt(H2_PRICE))
print("CAPEX batterie puissance (€)         :", fmt(CAPEX_BAT_POWER))
print("CAPEX batterie énergie (€)           :", fmt(CAPEX_BAT_ENERGY))
print("Durée de vie projet (années)         :", fmt(PROJECT_LIFETIME))
print("Taux d'actualisation (%)             :", fmt(DISCOUNT_RATE))

print("\n=== ⚙️ PARAMÈTRES TECHNIQUES ===")
print("Puissance batterie optimale (MW)     :", fmt(MAX_PWR_BAT))
print("Capacité batterie optimale (MWh)     :", fmt(MAX_CAPA_BAT))

print("\n=== 🔧 PERFORMANCE ÉLECTROLYSEUR ===")
print("Puissance moyenne électrolyseur (MW) :", fmt(MEAN_PWR_ELECTRO))
print("Coût moyen d'électricité (€/MW)      :", fmt(ELEC_COST_MEAN))

print("\n=== 🌱 HYDROGÈNE & CARBONE ===")
print("Production H2 annuelle (kg)          :", fmt(H2_TOTAL))
print("Intensité carbone moyenne (kg/kg)    :", fmt(CO2_INTENSITY_MEAN))
print("Émissions CO₂ totales (T)            :", fmt(CO2_TOTAL / 1000))

print("\n=== 💶 ÉCONOMIE ===")
print("Chiffre d'affaire annuel (€)         :", fmt(CA_TOTAL))
print("Coût total annuel (€)                :", fmt(TOTAL_COST))
print("Bénéfice annuel (€)                  :", fmt(BENEF_ANNUAL))
print("Cout de production de H2 optimisé (kg H2/€)              :", fmt(H2_COST_OPT))
print(df.head())