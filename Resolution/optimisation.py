"""File for the definition of the optimisation model"""

import sys
from pathlib import Path    

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("PROJECT_ROOT =", PROJECT_ROOT)

import pyomo.environ as pyo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from Data.constants import (  # noqa: E402
    H2_PRICE, 
    N,
    r,
    ELECTRO_MAX_PWR,
    CAPEX_PWR_BESS,
    CAPEX_EN_BESS

)
from Data.loading import (  # noqa: E402
    df,
    T
)
from Battery.battery_simulation import (  # noqa: E402
    power_balance_rule,
    soc_dyn_rule, 
    soc_lower_bound_rule, 
    soc_upper_bound_rule, 
    p_ch_limit_rule,
    p_dis_limit_rule,
    p_bat_max,
    e_bat_max
)

from Electrolyser.electrolyser_simulation import (  # noqa: E402
    el_max_rule,
    el_min_rule,
    el_ramp_rule,
    h2_production_rule,
    h2_target_rule,
)

from Costs.cost_functions import (  # noqa: E402
    objective_rule,
    cout_elec,
    emissions_co2
)

# ----------Creation of the model-----------------------------
model = pyo.ConcreteModel()
model.T = pyo.RangeSet(0, T-1)

# ---------Dimension variables--------------------------------
model.P_bat_max = pyo.Var(domain=pyo.NonNegativeReals) # Installed power of the BESS
model.E_bat_max = pyo.Var(domain=pyo.NonNegativeReals) # Energetic capacity of the battery system

# ---------Operational variables------------------------------
model.P_spot = pyo.Var(model.T, domain=pyo.Reals) # Buying is authorised
model.P_ch   = pyo.Var(model.T, domain=pyo.NonNegativeReals) # Charge power of the battery
model.P_dis  = pyo.Var(model.T, domain=pyo.NonNegativeReals) # Discharge power of the battery
model.P_electro   = pyo.Var(model.T, domain=pyo.NonNegativeReals) # Electrolyser power
model.SOC = pyo.Var(model.T, domain=pyo.NonNegativeReals) # Charging state of the battery (MWh)
model.H2 = pyo.Var(model.T, domain=pyo.NonNegativeReals) # H2 production

# ----------Constraints---------------------------------------
model.PowerBalance = pyo.Constraint(model.T, rule=power_balance_rule)
model.SOCdyn = pyo.Constraint(model.T, rule=soc_dyn_rule)
model.SOCLowerBound = pyo.Constraint(model.T, rule=soc_lower_bound_rule)
model.SOCUpperBound = pyo.Constraint(model.T, rule=soc_upper_bound_rule)
model.PchLimit = pyo.Constraint(model.T, rule=p_ch_limit_rule)
model.PdisLimit = pyo.Constraint(model.T, rule=p_dis_limit_rule)
model.PbatMax = pyo.Constraint(rule=p_bat_max)
model.EbatMax = pyo.Constraint(rule=e_bat_max)
model.ElMin = pyo.Constraint(model.T, rule=el_min_rule)
model.ElMax = pyo.Constraint(model.T, rule=el_max_rule)
model.ElRamp = pyo.Constraint(model.T, rule=el_ramp_rule)
model.H2Production = pyo.Constraint(model.T, rule=h2_production_rule)
model.H2Target = pyo.Constraint(rule=h2_target_rule)

# -----------Objective and solving----------------------------
model.Obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
solver = pyo.SolverFactory("highs")
result = solver.solve(model, tee=True)

# Use for debugging print(result.solver.status, result.solver.termination_condition)

def fmt(x):
    """
    Compact formatting for big number
    """
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


# ------Technical parameters---------------------
RES_MAX_PWR_BAT = fmt(pyo.value(model.P_bat_max))
RES_MAX_CAPA_BAT = fmt(pyo.value(model.E_bat_max))


# ------Electrolyser performance------------------------
RES_MEAN_PWR_ELECTRO = fmt(sum(pyo.value(model.P_electro[t]) for t in model.T) / len(model.T))
RES_TOTAL_PWR_ELECTRO = fmt(sum(pyo.value(model.P_electro[t]) for t in model.T))
RES_ELEC_COST_MEAN = fmt(pyo.value(cout_elec(model)) / RES_TOTAL_PWR_ELECTRO)

# ------Carbon and H2-----------------------------------
RES_H2_TOTAL = fmt(sum(pyo.value(model.H2[t]) for t in model.T))
RES_CO2_TOTAL = fmt(pyo.value(emissions_co2(model)))
RES_CO2_INTENSITY_MEAN = fmt(RES_CO2_TOTAL / (RES_H2_TOTAL*1000))

# ------Financial parameters----------------------------
RES_TOTAL_COST = fmt(pyo.value(model.Obj))
RES_LCOH_OPT = fmt(RES_TOTAL_COST / RES_H2_TOTAL)
RES_CA_TOTAL = fmt(RES_H2_TOTAL * H2_PRICE)
RES_BENEF_ANNUAL = fmt(RES_CA_TOTAL - RES_TOTAL_COST)

# ------Including the results in the dataset----------
# Note : will help trace different graphs
df["P_spot"] = pd.Series({t: pyo.value(model.P_spot[t]) for t in model.T})
df["P_ch"] = pd.Series({t: pyo.value(model.P_ch[t]) for t in model.T})
df["P_dis"] = pd.Series({t: pyo.value(model.P_dis[t]) for t in model.T})
df["P_electro"] = pd.Series({t: pyo.value(model.P_electro[t]) for t in model.T})
df["SOC"] = pd.Series({t: pyo.value(model.SOC[t]) for t in model.T})
df["H2"] = pd.Series({t: pyo.value(model.H2[t]) for t in model.T})