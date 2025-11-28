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



def optimisation_function(techno,prix_H2,P_electro_max,N,H2_target,Revente):
    C = modelConstants(techno, prix_H2, P_electro_max, N, H2_target, Revente)
    model = pyo.ConcreteModel()

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
    
    # Power Balance (m, t, C)
    model.PowerBalance = pyo.Constraint(model.T, rule=lambda m, t: power_balance_rule(m, t, C))
    # Battery SOC Dynamics (m, t, C)
    model.SOCdyn = pyo.Constraint(model.T, rule=lambda m, t: soc_dyn_rule(m, t, C))
    # Battery SOC lower bound (m, t, C)
    model.SOCLowerBound = pyo.Constraint(model.T, rule=lambda m, t: soc_lower_bound_rule(m, t, C))
    # Battery SOC upper bound (m, t, C)
    model.SOCUpperBound = pyo.Constraint(model.T, rule=lambda m, t: soc_upper_bound_rule(m, t, C))
    # Charge Power Limit (m, t, C)
    model.PchLimit = pyo.Constraint(model.T, rule=lambda m, t: p_ch_limit_rule(m, t, C))
    # Discharge Power Limit (m, t, C)
    model.PdisLimit = pyo.Constraint(model.T, rule=lambda m, t: p_dis_limit_rule(m, t, C))
    # Battery Power Installed Limit (m, C)
    model.PbatMax = pyo.Constraint(rule=lambda m: p_bat_max(m, C))
    # Battery Energy Installed Limit (m, C)
    model.EbatMax = pyo.Constraint(rule=lambda m: e_bat_max(m, C))
    # Electrolyser minimum load (m, t, C)
    model.ElMin = pyo.Constraint(model.T, rule=lambda m, t: el_min_rule(m, t, C))
    # Electrolyser maximum load (m, t, C)
    model.ElMax = pyo.Constraint(model.T, rule=lambda m, t: el_max_rule(m, t, C))
    # Electrolyser ramp constraint (m, t, C)
    model.ElRamp = pyo.Constraint(model.T, rule=lambda m, t: el_ramp_rule(m, t, C))
    # H2 production relation (m, t, C)
    model.H2Production = pyo.Constraint(model.T, rule=lambda m, t: h2_production_rule(m, t, C))
    # H2 annual target (m, C)
    model.H2Target = pyo.Constraint(rule=lambda m: h2_target_rule(m, C))
    # Objective function (m, C)
    model.Obj = pyo.Objective(rule=lambda m: objective_rule(m, C), sense=pyo.minimize)


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
    CAPEX_BAT_POWER      = C["c_bat_P"]
    CAPEX_BAT_ENERGY     = C["c_bat_E"]
    PROJECT_LIFETIME     = C["N"]
    DISCOUNT_RATE        = C["r"] * 100

    # === ⚙️ PARAMÈTRES TECHNIQUES ===
    MAX_PWR_BAT          = pyo.value(model.P_bat_max)
    MAX_CAPA_BAT         = pyo.value(model.E_bat_max)


    # === 🔧 PERFORMANCE ÉLECTROLYSEUR ===
    MEAN_PWR_ELECTRO     = sum(pyo.value(model.P_electro[t]) for t in model.T) / len(model.T)
    TOTAL_ENE_ELECTRO    = sum(pyo.value(model.P_electro[t]) for t in model.T) * C["dt"]
    ELEC_COST_MEAN       = sum(price_elec[t] * pyo.value(model.P_spot[t]) * C["dt"] for t in model.T) / TOTAL_ENE_ELECTRO
    EFFECTIVE_TIME       = TOTAL_ENE_ELECTRO / MAX_PWR_ELECTRO  # en heures
    EFFECTIVE_POWER      = MEAN_PWR_ELECTRO / MAX_PWR_ELECTRO * 100  # en %

    # === 🌱 HYDROGÈNE & CARBONE ===
    H2_TOTAL             = sum(pyo.value(model.H2[t]) for t in model.T)  # en kg
    CO2_TOTAL            = pyo.value(emissions_co2(model, C))
    CO2_INTENSITY        = CO2_TOTAL / H2_TOTAL



    # === 💶 ÉCONOMIE ===

    CA_TOTAL             = H2_TOTAL * prix_H2 - sum(price_elec[t] * min(0, pyo.value(model.P_spot[t])) * C["dt"] for t in model.T)
    CAPEX_COST           = pyo.value(capex_annual(model, C)) + C["c_electro"] * P_electro_max * C["alpha"]
    ELEC_COST            = sum(price_elec[t] * max(0, pyo.value(model.P_spot[t])) * C["dt"] for t in model.T)
    TOTAL_COST           = CAPEX_COST + ELEC_COST
    BENEF_ANNUAL         = CA_TOTAL - TOTAL_COST
    H2_COST              = TOTAL_COST / H2_TOTAL


    output_dic = {
        # === ⚙️ PARAMÈTRES D'ENTRÉES ===
        "H2_PRICE": H2_PRICE,
        "CAPEX_BAT_POWER": CAPEX_BAT_POWER,
        "CAPEX_BAT_ENERGY": CAPEX_BAT_ENERGY,
        "PROJECT_LIFETIME": PROJECT_LIFETIME,
        "DISCOUNT_RATE": DISCOUNT_RATE,
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

