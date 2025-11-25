"""File to define the constants of the model"""

# ---- INPUT PARAMETERS ----

techno = "PEM"             # Electrolyser technology: "AEL", "PEM", "SOEC"
prix_H2 = 10               # Price of green H2 in €/kg
P_electro_max = 100        # Electrolyser power in MW
N = 20                     # Project lifetime (years)
H2_target = 8_000_000     # Annual H2 production target (kg)
Revente = "YES"            # "YES" if electricity resale is possible, "NO" otherwise

# ---- MODEL CONSTANTS ----

dt = 1.0                     # Time step in hours

# Definition of electrolysis technologies
technos_electro = {
    "AEL": {
        "capex": 900_000,    # €/MW
        "rampe": 300,        # MW/h
        "yield": 20          # kg H2 / MWh
    },

    "PEM": {
        "capex": 1_400_000,
        "rampe": 600,
        "yield": 18
    },

    "SOEC": {
        "capex": 2_500_000,
        "rampe": 100,
        "yield": 27
    }
}

# Economic parameters
c_bat_P = 110_000     # Battery power CAPEX (€/MW)
c_bat_E = 120_000     # Battery energy CAPEX (€/MWh)
c_electro = technos_electro[techno]["capex"]  # Electrolyser CAPEX (€/MW)
r = 0.04              # Discount rate
alpha = r * (1 + r)**N / ((1 + r)**N - 1)   # Annuity factor

# Technical parameters
eta_electro = 0.7     # Overall electrolyser efficiency
eta_ch = 0.95         # Battery charging efficiency
eta_dis = 0.9         # Battery discharging efficiency

u_el_min = 0       # Minimum load fraction
u_el_max = 0.95    # Maximum load fraction

r_el = technos_electro[techno]["rampe"]  # Maximum electrolyser ramp rate (MW/h)
SOC_min = 0.1      # Minimum SOC (State of Charge) (fraction)
SOC_max = 0.95     # Maximum SOC (State of Charge) (fraction)

# Données H2
YIELD_H2 = technos_electro[techno]["yield"]        # kg/kWh


# Paramètres Prix à Terme
# prix_a_terme = 75   # Prix du contrat à terme pour 2024
# phi = 0.1            # Pourcentage de la puissance du forward