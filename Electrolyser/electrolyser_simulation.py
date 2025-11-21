"""Code for the simulation and functionning of the PEM electrolyser"""

from __future__ import annotations
from dataclasses import dataclass
import pyomo.environ as pyo

@dataclass
class ElectrolyserParams:
    PWR_H2_MAX: float = 100.0
    U_ELECTRO_MIN: float = 0.10
    U_ELECTRO_MAX: float = 0.95
    RAMP_ELECTRO: float = 1.0
    ELECTRO_YIELD: float = 0.70
    LHV_H2: float = 55.0
    dt: float = 1.0
    H2_TARGET: float = 1_000_000.0

@dataclass
class MarketParams:
    FORWARD_PRICE: float = 75.0

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
        if not hasattr(m, 'PWR_H2'):
            m.PWR_H2 = pyo.Var(self.T, domain=pyo.NonNegativeReals)
        if not hasattr(m, 'H2'):
            m.H2 = pyo.Var(self.T, domain=pyo.NonNegativeReals)
    
    # Constraints definition
    def add_constraints(self):
        m, p, T = self.m, self.p, list(self.T)

        # Functionning
        def el_min_rule(m, t):
            return m.PWR_H2[t] >= p.U_ELECTRO_MIN * p.PWR_H2_MAX
        m.ElMin = pyo.Constraint(self.T, rule=el_min_rule)

        def el_max_rule(m, t):
            return m.PWR_H2[t] <= p.U_ELECTRO_MAX * p.PWR_H2_MAX
        m.ElMax = pyo.Constraint(self.T, rule=el_max_rule)

        # Ramps
        def el_ramp_rule(m, t):
            if t == T[0]:
                return pyo.Constraint.Skip
            return pyo.inequality(-p.RAMP_ELECTRO, m.PWR_H2[t] - m.PWR_H2[t-1], p.RAMP_ELECTRO)
        m.ElRamp = pyo.Constraint(self.T, rule=el_ramp_rule)

        # H2 production
        def h2_production_rule(m, t):
            return m.H2[t] == p.ELECTRO_YIELD * m.PWR_H2[t] * p.dt * 1000.0 / p.LHV_H2
        m.H2Production = pyo.Constraint(self.T, rule=h2_production_rule)

        # Annual target
        def H2_TARGET_rule(m):
            return sum(m.H2[t] for t in self.T) >= p.H2_TARGET
        m.H2Target = pyo.Constraint(rule=H2_TARGET_rule)

class PowerBalanceBlock:
    """
    System power balance: 
      PWR_SPOT + PHI * PWR_H2_MAX = PWR_H2 + PWR_CHARGE - PWR_DISCHARGE
    Declares PWR_SPOT (purchase power profile) and PHI (forward contract share)
    """
    def __init__(self, m: pyo.ConcreteModel, T_set, PWR_H2_MAX: float, PHI_BOUNDS=(0.0, 1.0)):
        self.m = m
        self.T = T_set
        self.PWR_H2_MAX = PWR_H2_MAX
        self.PHI_BOUNDS = PHI_BOUNDS

    def add_variables(self):
        m = self.m
        if not hasattr(m, 'PWR_SPOT'):
            m.PWR_SPOT = pyo.Var(self.T, domain=pyo.NonNegativeReals) # Buying only
        if not hasattr(m, 'PHI'):
            m.PHI = pyo.Var(bounds=self.PHI_BOUNDS) # [0,1]

    def add_constraints(self):
        m = self.m
        PWR_H2_MAX = self.PWR_H2_MAX

        def power_balance_rule(m, t):
            return m.PWR_SPOT[t] + m.PHI * PWR_H2_MAX == m.PWR_H2[t] + m.PWR_CHARGE[t] - m.PWR_DISCHARGE[t]
        m.PowerBalance = pyo.Constraint(self.T, rule=power_balance_rule)
