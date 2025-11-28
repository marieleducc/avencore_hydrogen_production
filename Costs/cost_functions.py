"""Files for the definition of the objectives"""
from Data.constants import (
    ALPHA, 
    CAPEX_PWR_BESS, 
    CAPEX_EN_BESS, 
    dt,

    )
from Data.loading import CO2_INTENSITY, ELEC_PRICE

# -----Annualised CAPEX-------------------------------
def capex_annual(m):
    return ALPHA * (CAPEX_PWR_BESS * m.P_bat_max + CAPEX_EN_BESS * m.E_bat_max)

# -----Electricity price-----------------------------
def cout_elec(m):
    return sum(
        ELEC_PRICE[t] * m.P_spot[t] * dt
        for t in m.T
    )

# ----CO2 Emissions----------------------------------
def emissions_co2(m):
    return sum(
        CO2_INTENSITY[t] * m.P_spot[t] * dt
        for t in m.T
    )

# ----Annual total cost------------------------------
def objective_rule(m):
    return capex_annual(m) + cout_elec(m)