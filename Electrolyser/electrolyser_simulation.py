"""Files for the definition of the boundaries of the electrolyser"""
import pyomo.environ as pyo
from Data.constants import (
    U_ELECTRO_MAX, 
    U_ELECTRO_MIN,
    ELECTRO_MAX_PWR,
    RAMP_ELECTRO,
    ELECTRO_YIELD, 
    dt,
    LHV_H2, 
    H2_TARGET
    )

# ---------Functionning of the electrolyser---------------------
def el_min_rule(m, t):
    return m.P_electro[t] >= U_ELECTRO_MIN * ELECTRO_MAX_PWR

def el_max_rule(m, t):
    return m.P_electro[t] <= U_ELECTRO_MAX * ELECTRO_MAX_PWR

# ---------Ramps------------------------------------------------
def el_ramp_rule(m, t):
    if t == 0:
        return pyo.Constraint.Skip
    return pyo.inequality(-RAMP_ELECTRO, m.P_electro[t] - m.P_electro[t-1], RAMP_ELECTRO)

# -------Power/production relationship--------------------------
def h2_production_rule(m, t):
    return m.H2[t] == ELECTRO_YIELD * m.P_electro[t] * dt * 1000.0 / LHV_H2


# -------Annual target production-------------------------------
def h2_target_rule(m):
    return sum(m.H2[t] for t in m.T) >= H2_TARGET