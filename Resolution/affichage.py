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
print("Puissance électrolyseur max (MW)     :", fmt(MAX_PWR_ELECTRO))
print("Prix du kg de H2 (€)                 :", fmt(H2_PRICE))
print("CAPEX batterie puissance (€)         :", fmt(CAPEX_BAT_POWER))
print("CAPEX batterie énergie (€)           :", fmt(CAPEX_BAT_ENERGY))
print("Durée de vie projet (années)         :", fmt(PROJECT_LIFETIME))
print("Taux d'actualisation (%)             :", fmt(DISCOUNT_RATE))

print("\n=== ⚙️ PARAMÈTRES TECHNIQUES ===")
print("Puissance batterie optimale (MW)     :", fmt(MAX_PWR_BAT))
print("Capacité batterie optimale (MWh)     :", fmt(MAX_CAPA_BAT))

print("\n=== 🔧 PERFORMANCE ÉLECTROLYSEUR ===")
print("Puissance moyenne électrolyseur (MW) :", fmt(MEAN_PWR_ELECTRO))
print("Coût moyen d'électricité (€/MW)      :", fmt(ELEC_COST_MEAN))

print("\n=== 🌱 HYDROGÈNE & CARBONE ===")
print("Production H2 annuelle (kg)          :", fmt(H2_TOTAL))
print("Intensité carbone moyenne (kg/kg)    :", fmt(CO2_INTENSITY_MEAN))
print("Émissions CO₂ totales (T)            :", fmt(CO2_TOTAL / 1000))

print("\n=== 💶 ÉCONOMIE ===")
print("Chiffre d'affaire annuel (€)         :", fmt(CA_TOTAL))
print("Coût total annuel (€)                :", fmt(TOTAL_COST))
print("Bénéfice annuel (€)                  :", fmt(BENEF_ANNUAL))
print("Cout de production de H2 optimisé (kg H2/€)              :", fmt(H2_COST_OPT))
print(df.head())