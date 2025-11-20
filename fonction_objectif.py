def COST():
    return(P_terme * C_terme + (P_spot + P_charge)*C_spot)

# P_terme : puissance tirée du contrat à terme
# C_terme : coût du kWh contrat à terme
# P_spot : puissance tirée de SPOT vers l'électrolyseur
# P_charge : puissance tirée de SPOT vers le BESS
# C_spot : coût du kWh marché spot

