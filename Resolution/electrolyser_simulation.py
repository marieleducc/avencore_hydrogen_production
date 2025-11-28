"""Files for the definition of the boundaries of the electrolyser"""
import pyomo.environ as pyo

# --- 3.6 Électrolyseur : plage de fonctionnement ---
def el_min_rule(m, t, C):
    return m.P_electro[t] >= C["u_el_min"] * C["P_electro_max"] 
# model.ElMin = pyo.Constraint(model.T, rule=el_min_rule)

def el_max_rule(m, t, C):
    return m.P_electro[t] <= C["u_el_max"] * C["P_electro_max"]
# model.ElMax = pyo.Constraint(model.T, rule=el_max_rule)


# --- 3.7 Électrolyseur : rampes ---
def el_ramp_rule(m, t, C):
    if t == 0:
        # on peut imposer une condition initiale (par ex. démarrage à u_el_min*P_electro_max)
        return pyo.Constraint.Skip
    return pyo.inequality(-C["r_el"], m.P_electro[t] - m.P_electro[t-1], C["r_el"])

# model.ElRamp = pyo.Constraint(model.T, rule=el_ramp_rule)


# --- 3.8 H2 : relation puissance ↔ production ---
def h2_production_rule(m, t, C):
    # P_electro (MW) * dt (h) = MWh
    # MWh * YIELD_H2 (MWh/kg) = kg
    return m.H2[t] == C["YIELD_H2"] * C["eta_electro"] * m.P_electro[t] * C["dt"]
# model.H2Production = pyo.Constraint(model.T, rule=h2_production_rule)


# --- 3.9 Volume annuel cible H2 ---
def h2_target_rule(m, C):
    return sum(m.H2[t] for t in m.T) >= C["H2_target"]
# model.H2Target = pyo.Constraint(rule=h2_target_rule)