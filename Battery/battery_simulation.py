"""Function definition for the boundaries of BESS"""
import pyomo.environ as pyo
from Data.constants import *
from Data.loading import *

def soc_dyn_rule(m, t):
    if t == T-1:
        # dynamique de 0..T-1, on peut soit faire cyclique, soit ignorer le dernier pas
        return pyo.Constraint.Skip
    return m.SOC[t+1] == m.SOC[t] + eta_ch * m.P_ch[t] * dt - eta_dis * m.P_dis[t] * dt

# model.SOCdyn = pyo.Constraint(model.T, rule=soc_dyn_rule)


# --- 3.3 Batterie : bornes SOC ---
def soc_lower_bound_rule(m, t):
    return m.SOC[t] >= SOC_min * m.E_bat_max
# model.SOCLowerBound = pyo.Constraint(model.T, rule=soc_lower_bound_rule)

def soc_upper_bound_rule(m, t):
    return m.SOC[t] <= SOC_max * m.E_bat_max
# model.SOCUpperBound = pyo.Constraint(model.T, rule=soc_upper_bound_rule)


# --- 3.4 Batterie : puissance max charge / décharge ---
def p_ch_limit_rule(m, t):
    return m.P_ch[t] <= m.P_bat_max
# model.PchLimit = pyo.Constraint(model.T, rule=p_ch_limit_rule)

def p_dis_limit_rule(m, t):
    return m.P_dis[t] <= m.P_bat_max
# model.PdisLimit = pyo.Constraint(model.T, rule=p_dis_limit_rule)


# --- 3.5 Batterie : limite de la puissance et de la capacité de la batterie ---
def p_bat_max(m):
    return m.P_bat_max <= P_electro_max
# model.PbatMax = pyo.Constraint(rule=p_bat_max)

def e_bat_max(m):
    return m.E_bat_max <= 300
# model.EbatMax = pyo.Constraint(rule=e_bat_max)

# --- 3.1 Bilan de puissance ---

def power_balance_rule(m, t):
    return m.P_spot[t] == m.P_electro[t] + m.P_ch[t] - m.P_dis[t]
    # return m.P_spot[t] + phi * P_electro_max == m.P_electro[t] + m.P_ch[t] - m.P_dis[t]
# model.PowerBalance = pyo.Constraint(model.T, rule=power_balance_rule)


