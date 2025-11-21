"""Code for the simulation and functionning of the BESS"""

from __future__ import annotations
from dataclasses import dataclass
import pyomo.environ as pyo

@dataclass
class BatteryParams:
    CHARGE_YIELD: float = 1.0
    DISCHARGE_YIELD: float = 1.0 
    dt: float = 1.0
    SOC_MIN: float = 0.1
    SOC_MAX: float = 0.95

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
        if not hasattr(m, 'PWR_CHARGE'):
            m.PWR_CHARGE  = pyo.Var(self.T, domain=pyo.NonNegativeReals)
        if not hasattr(m, 'PWR_DISCHARGE'):
            m.PWR_DISCHARGE = pyo.Var(self.T, domain=pyo.NonNegativeReals)
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
            return m.SOC[t+1] == m.SOC[t] + p.CHARGE_YIELD*m.PWR_CHARGE[t]*p.dt - (1.0/p.DISCHARGE_YIELD)*m.PWR_DISCHARGE[t]*p.dt
        m.SOCdyn = pyo.Constraint(self.T, rule=soc_dyn_rule)

        # SOC's bounds
        def soc_lower_bound_rule(m, t):
            return m.SOC[t] >= p.SOC_MIN * m.EN_BAT_MAX
        m.SOCLowerBound = pyo.Constraint(self.T, rule=soc_lower_bound_rule)

        def soc_upper_bound_rule(m, t):
            return m.SOC[t] <= p.SOC_MAX * m.EN_BAT_MAX
        m.SOCUpperBound = pyo.Constraint(self.T, rule=soc_upper_bound_rule)

        # Power constraints
        def pwr_charge_limit_rule(m, t):
            return m.PWR_CHARGE[t] <= m.PWR_BAT_MAX
        m.PchLimit = pyo.Constraint(self.T, rule=pwr_charge_limit_rule)

        def pwr_discharge_limit_rule(m, t):
            return m.PWR_DISCHARGE[t] <= m.PWR_BAT_MAX
        m.PdisLimit = pyo.Constraint(self.T, rule=pwr_discharge_limit_rule)

        # Cycle condition
        def soc_cycle_rule(m):
            return m.SOC[T[0]] == m.SOC[T[-1]]
        m.SOCCycle = pyo.Constraint(rule=soc_cycle_rule)
