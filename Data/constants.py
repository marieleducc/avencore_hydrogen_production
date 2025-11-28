"""File to define the constants of the model"""

dt: float = 1.0 # Time step

H2_PRICE: float = 10.0 # Price of green H2
CAPEX_PWR_BESS: float = 110_000.0 # Power CAPEX of the BESS (€/MW)
CAPEX_EN_BESS: float = 120_000.0 # Energy CAPEX of the BESS(€/MWh)

# Annuity parameters
r: float = 0.04 # Actualisation rate
N: int = 20 # Project length (years)
ALPHA: float = r * (1 + r)**N / ((1 + r)**N - 1) # Annuity factor

# Technical parameters
ELECTRO_MAX_PWR: float = 100.0 # Electrolyser power (MW)
ELECTRO_YIELD: float = 1.0 # Global yield of the electrolyser
CHARGE_YIELD: float = 1.0 # Charge yield of the BESS
DISCHARGE_YIELD: float = 1.0 # Discharge yield of the BESS

U_ELECTRO_MIN: float = 0.0 # Minimal fraction of charge
U_ELECTRO_MAX: float = 0.95 # Maximal fraction of charge

RAMP_ELECTRO: float = 10.0 # Maximal ramp electrolyser (MW/h)        # rampe max électrolyseur (MW/h)
MIN_SOC: float = 0.1 # Min SOC (fraction)
MAX_SOC: float = 0.95 # Max SOC (fraction)

# Hydrogen data
LHV_H2: float = 55.0 # kWh/kg (PEM)
H2_TARGET: float = 10_000_000.0 # Annual H2 production target