"""Code for the simulation and functionning of the PEM electrolyser"""

from __future__ import annotations
from dataclasses import dataclass
import pyomo.environ as pyo

@dataclass
class ElectrolyserParams:
    P_hydro_max: float = 100.0
    u_el_min: float = 0.10
    u_el_max: float = 0.95
    r_el: float = 1.0       # rampe MW/h
    eta_el: float = 0.70
    LHV_H2: float = 55.0    # kWh/kg
    dt: float = 1.0
    H2_target: float = 1_000_000.0

@dataclass
class MarketParams:
    prix_a_terme: float = 75.0

class ElectrolyserBlock:
    """
    Declares the variables for the PEM electrolyser, and its constraints:
    - Min/Max of charge
    - Ramps
    - Relation of P with H2
    - Annual target for H2 production
    """
    def __init__(self, m: pyo.ConcreteModel, T_set, p: ElectrolyserParams):
        self.m = m
        self.T = T_set
        self.p = p

    # Variables definition
    def add_variables(self):
        m = self.m
        if not hasattr(m, 'P_hydro'):
            m.P_hydro = pyo.Var(self.T, domain=pyo.NonNegativeReals)
        if not hasattr(m, 'H2'):
            m.H2 = pyo.Var(self.T, domain=pyo.NonNegativeReals)
    
    # Constraints definition
    def add_constraints(self):
        m, p, T = self.m, self.p, list(self.T)

        # Functionning
        def el_min_rule(m, t):
            return m.P_hydro[t] >= p.u_el_min * p.P_hydro_max
        m.ElMin = pyo.Constraint(self.T, rule=el_min_rule)

        def el_max_rule(m, t):
            return m.P_hydro[t] <= p.u_el_max * p.P_hydro_max
        m.ElMax = pyo.Constraint(self.T, rule=el_max_rule)

        # Ramps
        def el_ramp_rule(m, t):
            if t == T[0]:
                return pyo.Constraint.Skip
            return pyo.inequality(-p.r_el, m.P_hydro[t] - m.P_hydro[t-1], p.r_el)
        m.ElRamp = pyo.Constraint(self.T, rule=el_ramp_rule)

        # H2 production
        def h2_production_rule(m, t):
            return m.H2[t] == p.eta_el * m.P_hydro[t] * p.dt * 1000.0 / p.LHV_H2
        m.H2Production = pyo.Constraint(self.T, rule=h2_production_rule)

        # Annual target
        def h2_target_rule(m):
            return sum(m.H2[t] for t in self.T) >= p.H2_target
        m.H2Target = pyo.Constraint(rule=h2_target_rule)

class PowerBalanceBlock:
    """
    System power balance: 
      P_spot + phi * P_hydro_max = P_hydro + P_ch - P_dis
    Declares P_spot (purchase power profile) and phi (forward contract share)
    """
    def __init__(self, m: pyo.ConcreteModel, T_set, P_hydro_max: float, phi_bounds=(0.0, 1.0)):
        self.m = m
        self.T = T_set
        self.P_hydro_max = P_hydro_max
        self.phi_bounds = phi_bounds

    def add_variables(self):
        m = self.m
        if not hasattr(m, 'P_spot'):
            m.P_spot = pyo.Var(self.T, domain=pyo.NonNegativeReals) # Buying only
        if not hasattr(m, 'phi'):
            m.phi = pyo.Var(bounds=self.phi_bounds) # [0,1]

    def add_constraints(self):
        m = self.m
        P_hydro_max = self.P_hydro_max

        def power_balance_rule(m, t):
            return m.P_spot[t] + m.phi * P_hydro_max == m.P_hydro[t] + m.P_ch[t] - m.P_dis[t]
        m.PowerBalance = pyo.Constraint(self.T, rule=power_balance_rule)
