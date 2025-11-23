"""Code for the definition of the different cost functions to include in the optimisation problem"""

from __future__ import annotations
from dataclasses import dataclass
import pyomo.environ as pyo

@dataclass
class EconomicParams:
    ELECTROLYSER_CAPEX: float = 700_000.0                   # €/MW_el
    CAPEX_PWR_BAT: float = 150_000.0                        # €/MW
    CAPEX_EN_BAT: float = 100_000.0                         # €/MWh
    FORWARD_PRICE: float = 75_000.0                         # €/MWh
    CO2_COST: float = 80.0                                  # €/tCO2
    ALPHA: float = 0.07 * (1+0.07)**15 / ((1+0.07)**15 - 1) # Annuity (r=7%, N=15)

class ObjectiveBuilder:
    """
    Builds the objective : annualised CAPEX + electricity cost + CO2
    """
    def __init__(self, m: pyo.ConcreteModel, T_set, ECON_PARA: EconomicParams, ELEC_PRICE, CO2_INTENSITY, dt: float = 1.0, include_co2: bool = False):
        self.m = m
        self.T = T_set
        self.ECON_PARA = ECON_PARA
        self.ELEC_PRICE = ELEC_PRICE            # Time-series of spot market electricity prices (€/MWh)
        self.CO2_INTENSITY = CO2_INTENSITY      # Time-series of grid carbon intensity (tCO2/MWh)
        self.dt = dt                            # Timestep of the simulation (hours)
        self.include_co2 = include_co2          # Boolean flag to include carbon costs in the objective function

    def capex_annual(self):
        m, e = self.m, self.ECON_PARA
        return e.ALPHA * (e.CAPEX_PWR_BAT * m.PWR_BAT_MAX + e.CAPEX_EN_BAT * m.EN_BAT_MAX)

    def cout_elec(self):
        m, e, dt, prix = self.m, self.ECON_PARA, self.dt, self.ELEC_PRICE
        # Forward cost (PHI * PWR_H2_MAX) + spot (PWR_SPOT)
        return sum((e.FORWARD_PRICE * m.PHI * 1.0 * dt + prix[t] * m.PWR_SPOT[t] * dt) for t in self.T)

    def emissions_co2(self):
        m, dt, I = self.m, self.dt, self.CO2_INTENSITY
        return sum(I[t] * m.PWR_SPOT[t] * dt for t in self.T)

    def build_objective(self):
        m, e = self.m, self.ECON_PARA
        base_cost = self.capex_annual() + self.cout_elec()
        if self.include_co2:
            base_cost += e.CO2_COST * self.emissions_co2()
        m.Obj = pyo.Objective(expr=base_cost, sense=pyo.minimize)
        return m.Obj
