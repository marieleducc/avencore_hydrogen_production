"""Function definition for the boundaries of BESS"""

import pyomo.environ as pyo
from Data.constants import (
    CHARGE_YIELD, 
    DISCHARGE_YIELD, 
    dt, 
    MIN_SOC,
    MAX_SOC,
    ELECTRO_MAX_PWR
    )
from Data.loading import T

# --------Dynamic SOC---------------------------------------
def soc_dyn_rule(m, t):
    if t == T-1:
        return pyo.Constraint.Skip
    return m.SOC[t+1] == m.SOC[t] + CHARGE_YIELD * m.P_ch[t] * dt - DISCHARGE_YIELD * m.P_dis[t] * dt

# ---------SOC bounds---------------------------------------
def soc_lower_bound_rule(m, t):
    return m.SOC[t] >= MIN_SOC * m.E_bat_max

def soc_upper_bound_rule(m, t):
    return m.SOC[t] <= MAX_SOC * m.E_bat_max

# ---------Maximal power for charge/discharge---------------
def p_ch_limit_rule(m, t):
    return m.P_ch[t] <= m.P_bat_max

def p_dis_limit_rule(m, t):
    return m.P_dis[t] <= m.P_bat_max

# --------Limits on the power and capacity of the battery---
def p_bat_max(m):
    return m.P_bat_max <= ELECTRO_MAX_PWR

def e_bat_max(m):
    return m.E_bat_max <= 300

# --------Power Balance-------------------------------------
def power_balance_rule(m, t):
    return m.P_spot[t] == m.P_electro[t] + m.P_ch[t] - m.P_dis[t]


