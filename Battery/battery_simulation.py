"""Code for the simulation and functionning of the BESS"""

from __future__ import annotations
from dataclasses import dataclass
import pyomo.environ as pyo

@dataclass
class BatteryParams:
    eta_ch: float = 1.0
    eta_dis: float = 1.0
    dt: float = 1.0
    SOC_min: float = 0.1
    SOC_max: float = 0.95

class BatteryBlock:
    """
    Declares the variables linked to the BESS, and adds constraints : 
    - Dynamic SOC
    - SOC's bounds
    - Power limits (charge/discharge)

    """
    def __init__(self, m: pyo.ConcreteModel, T_set, params: BatteryParams):
        self.m = m
        self.T = T_set
        self.p = params

    def add_variables(self):
        """
        Function to add the operational variables for the BESS

        """
        m = self.m
        if not hasattr(m, 'P_ch'):
            m.P_ch  = pyo.Var(self.T, domain=pyo.NonNegativeReals)
        if not hasattr(m, 'P_dis'):
            m.P_dis = pyo.Var(self.T, domain=pyo.NonNegativeReals)
        if not hasattr(m, 'SOC'):
            m.SOC   = pyo.Var(self.T, domain=pyo.NonNegativeReals)

    def add_constraints(self):
        """
        Definition of the constraints for the BESS
        """
        m, p, T = self.m, self.p, list(self.T)

        # Dynamic SOC
        def soc_dyn_rule(m, t):
            if t == T[-1]:
                return pyo.Constraint.Skip
            return m.SOC[t+1] == m.SOC[t] + p.eta_ch*m.P_ch[t]*p.dt - (1.0/p.eta_dis)*m.P_dis[t]*p.dt
        m.SOCdyn = pyo.Constraint(self.T, rule=soc_dyn_rule)

        # SOC's bounds
        def soc_lower_bound_rule(m, t):
            return m.SOC[t] >= p.SOC_min * m.E_bat_max
        m.SOCLowerBound = pyo.Constraint(self.T, rule=soc_lower_bound_rule)

        def soc_upper_bound_rule(m, t):
            return m.SOC[t] <= p.SOC_max * m.E_bat_max
        m.SOCUpperBound = pyo.Constraint(self.T, rule=soc_upper_bound_rule)

        # Power constraints
        def p_ch_limit_rule(m, t):
            return m.P_ch[t] <= m.P_bat_max
        m.PchLimit = pyo.Constraint(self.T, rule=p_ch_limit_rule)

        def p_dis_limit_rule(m, t):
            return m.P_dis[t] <= m.P_bat_max
        m.PdisLimit = pyo.Constraint(self.T, rule=p_dis_limit_rule)

        # Cycle condition
        def soc_cycle_rule(m):
            return m.SOC[T[0]] == m.SOC[T[-1]]
        m.SOCCycle = pyo.Constraint(rule=soc_cycle_rule)
