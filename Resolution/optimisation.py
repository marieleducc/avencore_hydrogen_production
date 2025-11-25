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
from Data.constants import *
from Data.loading import *
from Battery.battery_simulation import *
from Electrolyser.electrolyser_simulation import *
from Costs.cost_functions import *

model = pyo.ConcreteModel()

# ---- Sets ----
model.T = pyo.RangeSet(0, T-1)   # on utilise 0..T-1 pour faciliter les indices
# Pour les contraintes de rampe, on utilisera 1..T-1

# ---- Limitation Variables ----
model.P_bat_max = pyo.Var(domain=pyo.NonNegativeReals)  # Puissance installée batterie MW
model.E_bat_max = pyo.Var(domain=pyo.NonNegativeReals)  # Capacité énergétique de la batterie MWh
# model.phi = pyo.Var(domain=pyo.UnitInterval)            # fraction de la puissance de l'électrolyseur acheté sur le forward


# ---- Operational Variables ----
model.P_spot = pyo.Var(model.T, domain=pyo.NonNegativeReals)       # Puissance tirée au prix spot (Achat Uniquement)
# model.P_spot = pyo.Var(model.T, domain=pyo.Reals)                  # Achat Autoriser
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
RES_MAX_PWR_ELECTRO      = P_electro_max
RES_H2_PRICE             = prix_H2
RES_CAPEX_BAT_POWER      = c_bat_P
RES_CAPEX_BAT_ENERGY     = c_bat_E
RES_PROJECT_LIFETIME     = N
RES_DISCOUNT_RATE        = r * 100

print("\n===  📥 PARAMÈTRES D'ENTRÉE ===")
print("Puissance électrolyseur max (MW)     :", fmt(RES_MAX_PWR_ELECTRO))
print("Prix du kg de H2 (€)                 :", fmt(RES_H2_PRICE))
print("CAPEX batterie puissance (€)         :", fmt(RES_CAPEX_BAT_POWER))
print("CAPEX batterie énergie (€)           :", fmt(RES_CAPEX_BAT_ENERGY))
print("Durée de vie projet (années)         :", fmt(RES_PROJECT_LIFETIME))
print("Taux d'actualisation (%)             :", fmt(RES_DISCOUNT_RATE))

# === ⚙️ PARAMÈTRES TECHNIQUES ===
RES_MAX_PWR_BAT          = pyo.value(model.P_bat_max)
RES_MAX_CAPA_BAT         = pyo.value(model.E_bat_max)

print("\n=== ⚙️ PARAMÈTRES TECHNIQUES ===")
print("Puissance batterie optimale (MW)     :", fmt(RES_MAX_PWR_BAT))
print("Capacité batterie optimale (MWh)     :", fmt(RES_MAX_CAPA_BAT))

# === 🔧 PERFORMANCE ÉLECTROLYSEUR ===
RES_MEAN_PWR_ELECTRO     = sum(pyo.value(model.P_electro[t]) for t in model.T) / len(model.T)
RES_TOTAL_PWR_ELECTRO    = sum(pyo.value(model.P_electro[t]) for t in model.T)
RES_ELEC_COST_MEAN       = pyo.value(cout_elec(model)) / RES_TOTAL_PWR_ELECTRO

print("\n=== 🔧 PERFORMANCE ÉLECTROLYSEUR ===")
print("Puissance moyenne électrolyseur (MW) :", fmt(RES_MEAN_PWR_ELECTRO))
print("Coût moyen d'électricité (€/MW)      :", fmt(RES_ELEC_COST_MEAN))

# === 🌱 HYDROGÈNE & CARBONE ===
RES_H2_TOTAL             = sum(pyo.value(model.H2[t]) for t in model.T)
RES_CO2_TOTAL            = pyo.value(emissions_co2(model))
RES_CO2_INTENSITY_MEAN   = RES_CO2_TOTAL / RES_H2_TOTAL

print("\n=== 🌱 HYDROGÈNE & CARBONE ===")
print("Production H2 annuelle (kg)          :", fmt(RES_H2_TOTAL))
print("Intensité carbone moyenne (kg/kg)    :", fmt(RES_CO2_INTENSITY_MEAN))
print("Émissions CO₂ totales (T)            :", fmt(RES_CO2_TOTAL / 1000))

# === 💶 ÉCONOMIE ===
RES_TOTAL_COST           = pyo.value(model.Obj) + c_electro * P_electro_max * alpha
RES_H2_COST_OPT          = RES_H2_TOTAL / RES_TOTAL_COST
RES_CA_TOTAL             = RES_H2_TOTAL * prix_H2
RES_BENEF_ANNUAL         = RES_CA_TOTAL - RES_TOTAL_COST

print("\n=== 💶 ÉCONOMIE ===")
print("Chiffre d'affaire annuel (€)         :", fmt(RES_CA_TOTAL))
print("Coût total annuel (€)                :", fmt(RES_TOTAL_COST))
print("Bénéfice annuel (€)                  :", fmt(RES_BENEF_ANNUAL))
print("Cout de production de H2 optimisé (kg H2/€)              :", fmt(RES_H2_COST_OPT))
print(df.head())