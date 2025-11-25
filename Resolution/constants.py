def modelConstants(techno,prix_H2,P_electro_max,N,H2_target,Revente):
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

    constant_dic = {
        # === 💶 PARAMÈTRES ÉCONOMIQUES ===
        "c_bat_P": c_bat_P,               # Battery power CAPEX (€/MW)
        "c_bat_E": c_bat_E,               # Battery energy CAPEX (€/MWh)
        "c_electro": c_electro,           # Electrolyser CAPEX (€/MW)
        "r": r,                           # Discount rate
        "alpha": alpha,                   # Annuity factor

        # === ⚙️ PARAMÈTRES TECHNIQUES ===
        "eta_electro": eta_electro,       # Electrolyser efficiency
        "eta_ch": eta_ch,                 # Battery charging efficiency
        "eta_dis": eta_dis,               # Battery discharging efficiency

        "u_el_min": u_el_min,             # Minimum load fraction
        "u_el_max": u_el_max,             # Maximum load fraction

        "r_el": r_el,                     # Electrolyser ramp rate (MW/h)
        "SOC_min": SOC_min,               # Minimum State of Charge
        "SOC_max": SOC_max,               # Maximum State of Charge

        # === 🌱 PARAMÈTRES HYDROGÈNE ===
        "YIELD_H2": YIELD_H2,             # kg/kWh
    }
    
    return constant_dic


# Paramètres Prix à Terme
# prix_a_terme = 75   # Prix du contrat à terme pour 2024
    # phi = 0.1            # Pourcentage de la puissance du forward