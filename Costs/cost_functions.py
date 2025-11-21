"""Code for the definition of the different cost functions to include in the optimisation problem"""

from __future__ import annotations
from dataclasses import dataclass
import pyomo.environ as pyo

@dataclass
class EconomicParams:
    c_el: float = 700_000.0 # €/MW_el
    c_bat_P: float = 150.0 # €/MW
    c_bat_E: float = 10_000.0 # €/MWh
    prix_a_terme: float = 75.0 # €/MWh
    c_CO2: float = 80.0 # €/tCO2
    alpha: float = 0.07 * (1+0.07)**15 / ((1+0.07)**15 - 1) # Annuity (r=7%, N=15)

class ObjectiveBuilder:
    """
    Builds the objective : annualised CAPEX + electricity cost + CO2
    """
    def __init__(self, m: pyo.ConcreteModel, T_set, econ: EconomicParams, prix_elec, intensite_co2, dt: float = 1.0, include_co2: bool = False):
        self.m = m
        self.T = T_set
        self.econ = econ
        self.prix_elec = prix_elec
        self.intensite_co2 = intensite_co2
        self.dt = dt
        self.include_co2 = include_co2

    def capex_annual(self):
        m, e = self.m, self.econ
        return e.alpha * (e.c_bat_P * m.P_bat_max + e.c_bat_E * m.E_bat_max)

    def cout_elec(self):
        m, e, dt, prix = self.m, self.econ, self.dt, self.prix_elec
        # Forward cost (phi * P_hydro_max) + spot (P_spot)
        return sum((e.prix_a_terme * m.phi * 1.0 * dt + prix[t] * m.P_spot[t] * dt) for t in self.T)

    def emissions_co2(self):
        m, dt, I = self.m, self.dt, self.intensite_co2
        return sum(I[t] * m.P_spot[t] * dt for t in self.T)

    def build_objective(self):
        m, e = self.m, self.econ
        base_cost = self.capex_annual() + self.cout_elec()
        if self.include_co2:
            base_cost += e.c_CO2 * self.emissions_co2()
        m.Obj = pyo.Objective(expr=base_cost, sense=pyo.minimize)
        return m.Obj
