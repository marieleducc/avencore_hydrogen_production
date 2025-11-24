"""File to define the constants of the model"""

dt = 1.0                     # durée d'un pas de temps en heures

# Paramètres économiques
# prix_a_terme = 75   # Prix du contrat à terme pour 2024
# phi = 0.1            # Pourcentage de la puissance du forward
# c_el = 700000        # CAPEX électrolyseur (€/MW_el)

prix_H2 = 10           # Prix du kg de H2 vert en €
c_bat_P = 110_000     # CAPEX batterie puissance (€/MW)
c_bat_E = 120_000     # CAPEX batterie énergie (€/MWh)

# Paramètres d'annuitisation
r = 0.04              # taux d'actualisation
N = 20                # durée de vie projet (années)
alpha = r * (1 + r)**N / ((1 + r)**N - 1)   # facteur d'annuité

# Paramètres techniques
P_electro_max = 100     # Puissance de l'électrolyseur en MW
eta_electro = 1       # rendement global électrolyseur
eta_ch = 1         # rendement charge batterie
eta_dis = 1        # rendement décharge batterie

u_el_min = 0     # fraction minimale de charge
u_el_max = 0.95    # fraction maximale de charge

r_el = 10         # rampe max électrolyseur (MW/h)
SOC_min = 0.1      # SOC min (fraction)
SOC_max = 0.95     # SOC max (fraction)

# Données H2
LHV_H2 = 55        # kWh/kg (PEM)
H2_target = 10_000_000 # objectif annuel de production H2 (kg) à adapter