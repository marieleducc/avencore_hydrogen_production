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
 
# ---------- PARAMÈTRES GLOBAUX (à garder cohérents) ----------
 
CAPEX_PWR_BAT = 150.0      # €/kW ou €/MW selon tes unités (reste cohérente)
CAPEX_EN_BAT = 10_000.0    # €/MWh
r = 0.07
N_years = 15
ALPHA = r * (1 + r) ** N_years / ((1 + r) ** N_years - 1)
 
# Électrolyseur
ELECTRO_MAX_PWR = 100.0      # MW (reste sur un ordre de grandeur réaliste)
U_ELECTRO_MAX = 0.95
RAMP_ELECTRO = 10.0        # MW/step
ELECTRO_YIELD = 0.70
LHV_H2 = 55.0              # kWh/kg
DT = 1.0                   # **1 heure par pas de temps, surtout pas 8760 !**
 
SOC_MIN = 0.10
SOC_MAX = 0.95
CHARGE_YIELD = 1.0
DISCHARGE_YIELD = 1.0
 
 
def local_cost(P_bat_max: float, E_bat_max: float, elec_price) -> float:
    """
    Problème local : pour un dimensionnement (P_bat_max, E_bat_max),
    on résout l’optimisation d’exploitation et on renvoie :
        coût = CAPEX_annuel_batterie + coût électricité
 
    Pour stabiliser :
    - dt = 1 h
    - H2_TARGET calculé de façon cohérente avec la puissance max
    """
 
    # 0) Série temporelle & prix
    if isinstance(elec_price, dict):
        T_list = sorted(elec_price.keys())
        price = {t: float(elec_price[t]) for t in T_list}
    else:
        T_list = list(range(len(elec_price)))
        price = {t: float(elec_price[t]) for t in T_list}
 
    nb_h = len(T_list)
 
    # 1) H₂ TARGET COHÉRENT
    # production max théorique sur l’horizon :
    # ELECTRO_MAX_PWR [MW] * U_ELECTRO_MAX * nb_h [h] * 1000 / LHV [kWh/kg]
    h2_max_theorique = (
        ELECTRO_YIELD * U_ELECTRO_MAX * ELECTRO_MAX_PWR * nb_h * DT * 1000.0 / LHV_H2
    )
    # on demande par ex. 80 % de cette valeur, pour que ce soit faisable
    H2_TARGET = 0.8 * h2_max_theorique
 
    m = pyo.ConcreteModel()
    m.T = pyo.Set(initialize=T_list)
    T = T_list
 
    # 2) Variables de dimensionnement, fixées par le GA
    m.P_bat_max = pyo.Var(domain=pyo.NonNegativeReals)
    m.E_bat_max = pyo.Var(domain=pyo.NonNegativeReals)
    m.P_bat_max.fix(P_bat_max)
    m.E_bat_max.fix(E_bat_max)
 
    # 3) Variables opérationnelles
    m.P_spot = pyo.Var(m.T, domain=pyo.Reals)
    m.P_electro = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.P_ch = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.P_dis = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.SOC = pyo.Var(m.T, domain=pyo.NonNegativeReals)
    m.H2 = pyo.Var(m.T, domain=pyo.NonNegativeReals)
 
    # ---------- ÉLECTROLYSEUR ----------
 
    # borne max
    def el_max_rule(m, t):
        return m.P_electro[t] <= U_ELECTRO_MAX * ELECTRO_MAX_PWR
    m.ElMax = pyo.Constraint(m.T, rule=el_max_rule)
 
    # rampes
    def el_ramp_rule(m, t):
        if t == T[0]:
            return pyo.Constraint.Skip
        return pyo.inequality(
            -RAMP_ELECTRO,
            m.P_electro[t] - m.P_electro[t - 1],
            RAMP_ELECTRO,
        )
    m.ElRamp = pyo.Constraint(m.T, rule=el_ramp_rule)
 
    # production H2
    def h2_prod_rule(m, t):
        # H2 [kg] = η * P [MW] * dt [h] * 1000 / LHV [kWh/kg]
        return m.H2[t] == ELECTRO_YIELD * m.P_electro[t] * DT * 1000.0 / LHV_H2
    m.H2Prod = pyo.Constraint(m.T, rule=h2_prod_rule)
 
    # cible H2 réaliste
    def h2_target_rule(m):
        return sum(m.H2[t] for t in m.T) >= H2_TARGET
    m.H2Target = pyo.Constraint(rule=h2_target_rule)
 
    # ---------- BATTERIE ----------
 
    # dynamique SOC
    def soc_dyn_rule(m, t):
        if t == T[-1]:
            return pyo.Constraint.Skip
        return m.SOC[t + 1] == (
            m.SOC[t]
            + CHARGE_YIELD * m.P_ch[t] * DT
            - (1.0 / DISCHARGE_YIELD) * m.P_dis[t] * DT
        )
    m.SOCDyn = pyo.Constraint(m.T, rule=soc_dyn_rule)
 
    # SOC min / max
    def soc_min_rule(m, t):
        return m.SOC[t] >= SOC_MIN * m.E_bat_max
    m.SOCMin = pyo.Constraint(m.T, rule=soc_min_rule)
 
    def soc_max_rule(m, t):
        return m.SOC[t] <= SOC_MAX * m.E_bat_max
    m.SOCMax = pyo.Constraint(m.T, rule=soc_max_rule)
 
    # P_ch, P_dis bornés par P_bat_max
    def p_ch_lim_rule(m, t):
        return m.P_ch[t] <= m.P_bat_max
    m.PchLim = pyo.Constraint(m.T, rule=p_ch_lim_rule)
 
    def p_dis_lim_rule(m, t):
        return m.P_dis[t] <= m.P_bat_max
    m.PdisLim = pyo.Constraint(m.T, rule=p_dis_lim_rule)
 
    # cycle SOC
    def soc_cycle_rule(m):
        return m.SOC[T[0]] == m.SOC[T[-1]]
    m.SOCCycle = pyo.Constraint(rule=soc_cycle_rule)
 
    # ---------- BILAN DE PUISSANCE ----------
    def power_balance_rule(m, t):
        return m.P_spot[t] == m.P_electro[t] + m.P_ch[t] - m.P_dis[t]
    m.PowerBalance = pyo.Constraint(m.T, rule=power_balance_rule)
 
    # ---------- OBJECTIF ----------
    capex_annuel = ALPHA * (
        CAPEX_PWR_BAT * m.P_bat_max + CAPEX_EN_BAT * m.E_bat_max
    )
    cout_elec = sum(price[t] * m.P_spot[t] * DT for t in m.T)
    m.Obj = pyo.Objective(expr=capex_annuel + cout_elec, sense=pyo.minimize)
 
    # ---------- RÉSOLUTION ----------
    solver = pyo.SolverFactory("glpk")
    try:
        res = solver.solve(m, tee=False)
    except Exception:
        return 1e15  # plantage solveur = grosse pénalité
 
    term = res.solver.termination_condition
    if term not in (
        pyo.TerminationCondition.optimal,
        pyo.TerminationCondition.locallyOptimal,
    ):
        # infaisable, non convergé → pénalité
        return 1e14
 
    # Si tu veux vérifier que H2 est dans des ordres raisonnables :
    # total_h2 = sum(pyo.value(m.H2[t]) for t in m.T)
    # print("Total H2 produit :", total_h2)
 
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
        ALPHA = random.random()
        c1 = [ALPHA * p1[i] + (1 - ALPHA) * p2[i] for i in range(n_vars)]
        c2 = [(1 - ALPHA) * p1[i] + ALPHA * p2[i] for i in range(n_vars)]
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
    # Exemple : série de prix sur 24h (sinusoïde)
    N = 24
    elec_price = {
        t: 50.0 + 20.0 * np.sin(2 * np.pi * t / 24.0) for t in range(N)
    }
 
    # Bornes de dimensionnement batterie
    bounds = [
        (0.0, 50.0),   # P_bat_max entre 0 et 50 MW
        (0.0, 200.0),  # E_bat_max entre 0 et 200 MWh
    ]
 
    best_x, best_f = genetic_algorithm(
        elec_price=elec_price,
        bounds=bounds,
        pop_size=8,         # commence petit pour tester
        n_generations=5,
        p_crossover=0.8,
        p_mutation=0.2,
        rng_seed=123,
    )
 
    print("\n=== Résultat final du GA ===")
    print(f"P_bat_max* = {best_x[0]:.3f} MW")
    print(f"E_bat_max* = {best_x[1]:.3f} MWh")
    print(f"Coût minimal ≈ {best_f:.2f}")