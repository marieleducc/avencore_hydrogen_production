# meta_optimisation.py
"""
Optimisation méta-heuristique (algorithme génétique) pour dimensionner la batterie
(P_bat_max, E_bat_max) en minimisant les coûts (CAPEX + électricité).
 
- Pas de classes : tout est en fonctions + constantes globales.
- local_cost(P_bat_max, E_bat_max, elec_price) résout un problème Pyomo "local"
  (exploitation optimale de l'électrolyseur + batterie pour un horizon temporel).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import random
import numpy as np
import pyomo.environ as pyo

# ========= PARAMÈTRES TECHNO-ÉCO (à ajuster à ton cas) =========
 
# Batterie
CAPEX_PWR_BAT = 150.0      # €/kW (ou €/MW, à homogénéiser)
CAPEX_EN_BAT = 10_000.0    # €/MWh
r = 0.07                   # taux d'actualisation
N_years = 15               # durée de vie
ALPHA = r * (1 + r) ** N_years / ((1 + r) ** N_years - 1)  # facteur d'annuité
 
# Électrolyseur
P_ELECTRO_MAX = 100.0      # MW
U_ELECTRO_MAX = 0.95
RAMP_ELECTRO = 10.0        # MW par pas
ELECTRO_YIELD = 0.70       # rendement global
LHV_H2 = 55.0              # kWh/kg
H2_TARGET = 1_000_000.0    # kg sur l'horizon
 
# Batterie – techno
SOC_MIN = 0.10
SOC_MAX = 0.95
ETA_CH = 1.0
ETA_DIS = 1.0
DT = 1.0                   # h
 
 
# ========= 1. PROBLÈME LOCAL (Pyomo) =========
 
def local_cost(P_bat_max: float, E_bat_max: float, elec_price) -> float:
    """
    Problème local de dispatch sur l'horizon :
      - variables : P_spot[t], P_electro[t], P_ch[t], P_dis[t], SOC[t], H2[t]
      - contraintes : électrolyseur, batterie, bilan de puissance, H2 cible
      - objectif : CAPEX annuel batterie + coût d'électricité
 
    Paramètres
    ----------
    P_bat_max : float
        Puissance nominale de la batterie [MW].
    E_bat_max : float
        Capacité énergétique de la batterie [MWh].
    elec_price : dict ou array-like
        Prix de l'électricité par pas de temps (€/MWh).
 
    Retour
    ------
    float : coût total (CAPEX annuel + coût élec),
            ou une grosse pénalité si le modèle est infaisable.
    """
    # --- Série temporelle ---
    if isinstance(elec_price, dict):
        T_list = sorted(elec_price.keys())
        price = {t: float(elec_price[t]) for t in T_list}
    else:
        T_list = list(range(len(elec_price)))
        price = {t: float(elec_price[t]) for t in T_list}
 
    m = pyo.ConcreteModel()
    m.T = pyo.Set(initialize=T_list)
    T = T_list
 
    # --- Variables de dimensionnement (fixées) ---
    m.P_bat_max = pyo.Var(domain=pyo.NonNegativeReals)
    m.E_bat_max = pyo.Var(domain=pyo.NonNegativeReals)
    m.P_bat_max.fix(P_bat_max)
    m.E_bat_max.fix(E_bat_max)
 
    # --- Variables opérationnelles ---
    m.P_spot = pyo.Var(m.T, domain=pyo.Reals)            # achat/vente possible
    m.P_electro = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.P_ch = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.P_dis = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.SOC = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.H2 = pyo.Var(m.T, domain=pyo.NonNegativeReals)
 
    # ---------- Contraintes électrolyseur ----------
 
    def el_max_rule(m, t):
        return m.P_electro[t] <= U_ELECTRO_MAX * P_ELECTRO_MAX
    m.ElMax = pyo.Constraint(m.T, rule=el_max_rule)
 
    def el_ramp_rule(m, t):
        if t == T[0]:
            return pyo.Constraint.Skip
        return pyo.inequality(
            -RAMP_ELECTRO,
            m.P_electro[t] - m.P_electro[t - 1],
            RAMP_ELECTRO
        )
    m.ElRamp = pyo.Constraint(m.T, rule=el_ramp_rule)
 
    def h2_prod_rule(m, t):
        # H2 [kg] = rendement * P (MW) * dt (h) * 1000 / LHV (kWh/kg)
        return m.H2[t] == ELECTRO_YIELD * m.P_electro[t] * DT * 1000.0 / LHV_H2
    m.H2Prod = pyo.Constraint(m.T, rule=h2_prod_rule)
 
    def h2_target_rule(m):
        return sum(m.H2[t] for t in m.T) >= H2_TARGET
    m.H2Target = pyo.Constraint(rule=h2_target_rule)
 
    # ---------- Batterie : dynamique SOC ----------
 
    def soc_dyn_rule(m, t):
        if t == T[-1]:
            return pyo.Constraint.Skip
        return m.SOC[t + 1] == (
            m.SOC[t]
            + ETA_CH * m.P_ch[t] * DT
            - (1.0 / ETA_DIS) * m.P_dis[t] * DT
        )
    m.SOCDyn = pyo.Constraint(m.T, rule=soc_dyn_rule)
 
    # Bornes SOC
    def soc_min_rule(m, t):
        return m.SOC[t] >= SOC_MIN * m.E_bat_max
    m.SOCMin = pyo.Constraint(m.T, rule=soc_min_rule)
 
    def soc_max_rule(m, t):
        return m.SOC[t] <= SOC_MAX * m.E_bat_max
    m.SOCMax = pyo.Constraint(m.T, rule=soc_max_rule)
 
    # Puissance batterie
    def p_ch_lim_rule(m, t):
        return m.P_ch[t] <= m.P_bat_max
    m.PchLim = pyo.Constraint(m.T, rule=p_ch_lim_rule)
 
    def p_dis_lim_rule(m, t):
        return m.P_dis[t] <= m.P_bat_max
    m.PdisLim = pyo.Constraint(m.T, rule=p_dis_lim_rule)
 
    # Cycle de SOC
    def soc_cycle_rule(m):
        return m.SOC[T[0]] == m.SOC[T[-1]]
    m.SOCCycle = pyo.Constraint(rule=soc_cycle_rule)
 
    # ---------- Bilan de puissance ----------
    def power_balance_rule(m, t):
        # P_spot = P_electro + P_ch - P_dis
        return m.P_spot[t] == m.P_electro[t] + m.P_ch[t] - m.P_dis[t]
    m.PowerBalance = pyo.Constraint(m.T, rule=power_balance_rule)
 
    # ---------- Objectif ----------
    capex_annuel = ALPHA * (
        CAPEX_PWR_BAT * m.P_bat_max + CAPEX_EN_BAT * m.E_bat_max
    )
    cout_elec = sum(price[t] * m.P_spot[t] * DT for t in m.T)
 
    m.Obj = pyo.Objective(expr=capex_annuel + cout_elec, sense=pyo.minimize)
 
    # ---------- Résolution ----------
    solver = pyo.SolverFactory("glpk")
    try:
        res = solver.solve(m, tee=False)
    except Exception:
        # si le solveur plante, on renvoie une grosse pénalité
        return 1e15
 
    term = res.solver.termination_condition
    if term not in (
        pyo.TerminationCondition.optimal,
        pyo.TerminationCondition.locallyOptimal,
    ):
        # infaisable, non convergé, etc. → pénalité
        return 1e14
 
    return pyo.value(m.Obj)
 
 
# ========= 2. FITNESS POUR LE GA =========
 
def fitness(candidate, elec_price):
    """
    candidate = [P_bat_max, E_bat_max]
    """
    P_bat_max, E_bat_max = candidate
    return local_cost(P_bat_max, E_bat_max, elec_price)
 
 
# ========= 3. ALGorithme GÉNÉTIQUE =========
 
def genetic_algorithm(
    elec_price,
    bounds,
    pop_size=20,
    n_generations=30,
    p_crossover=0.8,
    p_mutation=0.2,
    rng_seed=42,
):
    """
    Algorithme génétique continu sur 2 variables :
      x = [P_bat_max, E_bat_max]
 
    bounds = [(P_min, P_max), (E_min, E_max)]
    """
    random.seed(rng_seed)
    np.random.seed(rng_seed)
    n_vars = len(bounds)
 
    def random_candidate():
        return [
            random.uniform(bounds[i][0], bounds[i][1]) for i in range(n_vars)
        ]
 
    # Population initiale
    population = [random_candidate() for _ in range(pop_size)]
    fitness_values = [fitness(ind, elec_price) for ind in population]
 
    # Sélection par tournoi
    def tournament_selection(k=3):
        idxs = random.sample(range(pop_size), k)
        best_idx = min(idxs, key=lambda i: fitness_values[i])
        return population[best_idx][:]
 
    # Croisement
    def crossover(p1, p2):
        if random.random() > p_crossover:
            return p1[:], p2[:]
        alpha = random.random()
        c1 = [alpha * p1[i] + (1 - alpha) * p2[i] for i in range(n_vars)]
        c2 = [(1 - alpha) * p1[i] + alpha * p2[i] for i in range(n_vars)]
        return c1, c2
 
    # Mutation
    def mutate(ind):
        for i in range(n_vars):
            if random.random() < p_mutation:
                sigma = 0.1 * (bounds[i][1] - bounds[i][0])
                ind[i] += random.gauss(0, sigma)
                ind[i] = max(bounds[i][0], min(bounds[i][1], ind[i]))
 
    # Boucle GA
    for gen in range(n_generations):
        new_pop = []
 
        # Élitisme : on garde le meilleur
        best_idx = int(np.argmin(fitness_values))
        best_ind = population[best_idx][:]
        best_fit = fitness_values[best_idx]
        new_pop.append(best_ind)
 
        while len(new_pop) < pop_size:
            p1 = tournament_selection()
            p2 = tournament_selection()
            c1, c2 = crossover(p1, p2)
            mutate(c1)
            mutate(c2)
            new_pop.append(c1)
            if len(new_pop) < pop_size:
                new_pop.append(c2)
 
        population = new_pop[:pop_size]
        fitness_values = [fitness(ind, elec_price) for ind in population]
 
        print(
            f"Génération {gen+1}/{n_generations} - "
            f"meilleur coût = {min(fitness_values):.2f}"
        )
 
    best_idx = int(np.argmin(fitness_values))
    best_candidate = population[best_idx]
    best_cost = fitness_values[best_idx]
    return best_candidate, best_cost
 
 
# ========= 4. EXEMPLE D'UTILISATION =========
if __name__ == "__main__":

    import pandas as pd
 
    # 1) Charger le fichier de données

    # adapte le chemin si besoin (par ex. "./Data/data.csv" ou "../Data/data.csv")

    PATH = PROJECT_ROOT / "Data" / "data.csv"

    df = pd.read_csv(PATH)
 
    # 2) Récupérer la colonne de prix spot

    # remplace "Spot_Price" si ta colonne a un autre nom

    spot = df["Spot_Price"]
 
    # 3) Construire elec_price sous forme de dict {t: prix}

    elec_price = {t: float(spot.iloc[t]) for t in range(len(spot))}
 
    # 4) Définir les bornes de dimensionnement de la batterie

    bounds = [

        (0.0, 50.0),   # P_bat_max entre 0 et 50 MW (à ajuster)

        (0.0, 200.0),  # E_bat_max entre 0 et 200 MWh (à ajuster)

    ]
 
    # 5) Lancer l'algorithme génétique

    best_x, best_f = genetic_algorithm(

        elec_price=elec_price,

        bounds=bounds,

        pop_size=10,       # tu peux augmenter après les tests

        n_generations=10,  # idem

        p_crossover=0.8,

        p_mutation=0.2,

        rng_seed=123,

    )
 
    print("\n=== Résultat final du GA ===")

    print(f"P_bat_max* = {best_x[0]:.3f} MW")

    print(f"E_bat_max* = {best_x[1]:.3f} MWh")

    print(f"Coût minimal ≈ {best_f:.2f}")

 