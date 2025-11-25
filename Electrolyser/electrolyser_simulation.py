"""Files for the definition of the boundaries of the electrolyser"""
import pyomo.environ as pyo
from Data.constants import *

# --- 3.6 Électrolyseur : plage de fonctionnement ---
def el_min_rule(m, t):
    return m.P_electro[t] >= u_el_min * P_electro_max
# model.ElMin = pyo.Constraint(model.T, rule=el_min_rule)

def el_max_rule(m, t):
    return m.P_electro[t] <= u_el_max * P_electro_max
# model.ElMax = pyo.Constraint(model.T, rule=el_max_rule)


# --- 3.7 Électrolyseur : rampes ---
def el_ramp_rule(m, t):
    if t == 0:
        # on peut imposer une condition initiale (par ex. démarrage à u_el_min*P_electro_max)
        return pyo.Constraint.Skip
    return pyo.inequality(-r_el, m.P_electro[t] - m.P_electro[t-1], r_el)

# model.ElRamp = pyo.Constraint(model.T, rule=el_ramp_rule)


# --- 3.8 H2 : relation puissance ↔ production ---
def h2_production_rule(m, t):
    # P_electro (MW) * dt (h) = MWh
    # MWh * YIELD_H2 (MWh/kg) = kg
    return m.H2[t] == YIELD_H2 * eta_electro * m.P_electro[t] * dt
# model.H2Production = pyo.Constraint(model.T, rule=h2_production_rule)


# --- 3.9 Volume annuel cible H2 ---
def h2_target_rule(m):
    return sum(m.H2[t] for t in m.T) >= H2_target
# model.H2Target = pyo.Constraint(rule=h2_target_rule)