"""Files for the definition of the objectives"""
from Resolution.loading import intensity_elec, price_elec

# -- Helper : CAPEX annualisé --
def capex_annual(m, C):
    return C["alpha"] * (C["c_bat_P"] * m.P_bat_max + C["c_bat_E"] * m.E_bat_max)

# -- Helper : coût électricité --
def cout_elec(m, C):
    return sum(
        price_elec[t] * m.P_spot[t] * C["dt"]
        # (prix_a_terme * phi * P_electro_max + price_elec[t] * m.P_spot[t]) * dt
        for t in m.T
    )

# -- Helper : émissions de CO2 --
def emissions_co2(m, C):
    return sum(
        intensity_elec[t] * m.P_spot[t] * C["dt"]
        for t in m.T
    )


# -- Objectif : coût total annuel --
def objective_rule(m, C):
    return capex_annual(m, C) + cout_elec(m, C)
 
# model.Obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)