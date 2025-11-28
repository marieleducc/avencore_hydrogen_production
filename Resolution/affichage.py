import plotly.graph_objs as go
import pandas as pd
import numpy as np
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Resolution.optimisation import optimisation_function


C, df = optimisation_function("AEL",7,100,10,10000000,"NO")

def fmt(x):
    """Format compact pour grands nombres : 1.2M, 7.5k, 9.3B ou 123.45."""
    if abs(x) >= 1e9:
        return f"{round(x)/1e9:.0f} B"
    elif abs(x) >= 1e6:
        return f"{round(x)/1e6:.0f} M"
    elif abs(x) >= 1e3:
        return f"{round(x)/1e3:.0f} k"
    elif abs(x) >= 1e2:
        return f"{round(x):.0f}"
    elif abs(x) >= 1e1:
        return f"{round(x):.0f}"
    else:
        return f"{x:.2f}"


print("\n===  📥 PARAMÈTRES D'ENTRÉE ===")
print("Puissance électrolyseur max (MW)     :", fmt(C["MAX_PWR_ELECTRO"]))
print("Prix du kg de H2 (€)                 :", fmt(C["H2_PRICE"]))
print("CAPEX batterie puissance (€)         :", fmt(C["CAPEX_BAT_POWER"]))
print("CAPEX batterie énergie (€)           :", fmt(C["CAPEX_BAT_ENERGY"]))
print("Durée de vie projet (années)         :", fmt(C["PROJECT_LIFETIME"]))
print("Taux d'actualisation (%)             :", fmt(C["DISCOUNT_RATE"]))

print("\n=== ⚙️ PARAMÈTRES TECHNIQUES ===")
print("Puissance batterie optimale (MW)     :", fmt(C["MAX_PWR_BAT"]))
print("Capacité batterie optimale (MWh)     :", fmt(C["MAX_CAPA_BAT"]))

print("\n=== 🔧 PERFORMANCE ÉLECTROLYSEUR ===")
print("Puissance moyenne électrolyseur (MW) :", fmt(C["MEAN_PWR_ELECTRO"]))
print("Coût moyen d'électricité (€/MW)      :", fmt(C["ELEC_COST_MEAN"]))

print("\n=== 🌱 HYDROGÈNE & CARBONE ===")
print("Production H2 annuelle (kg)          :", fmt(C["H2_TOTAL"]))
print("Intensité carbone moyenne (kg/kg)    :", fmt(C["CO2_INTENSITY_MEAN"]))
print("Émissions CO₂ totales (T)            :", fmt(C["CO2_TOTAL"] / 1000)) # Note : Le calcul de division par 1000 est conservé

print("\n=== 💶 ÉCONOMIE ===")
print("Chiffre d'affaire annuel (€)         :", fmt(C["CA_TOTAL"]))
print("Coût total annuel (€)                :", fmt(C["TOTAL_COST"]))
print("Bénéfice annuel (€)                  :", fmt(C["BENEF_ANNUAL"]))
print("Cout de production de H2 optimisé (kg H2/€)              :", fmt(C["H2_COST_OPT"]))

print(df.head())