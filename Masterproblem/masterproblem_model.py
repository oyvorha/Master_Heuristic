from gurobipy import *
import time
import numpy as np


def run_model(model_manager, fixed):

    try:
        m = Model("Heuristic")
        m.setParam('TimeLimit', 60 * 60)
        start_time = time.time()

        # ------ SETS -----------------------------------------------------------------------------
        Stations = model_manager.stations
        Swap_Stations = Stations[1:-1]
        Vehicles = model_manager.vehicles
        Routes = model_manager.routes
        Patterns = model_manager.patterns
        Scenarios = fixed.scenarios

        # ------ PARAMETERS -----------------------------------------------------------------------
        A = model_manager.origin_matrix
        C = model_manager.subproblem_objectives
        P = fixed.scenarios.probabilities
        Q_FCL = model_manager.pattern_fcl
        Q_CCL = model_manager.pattern_ccl
        Q_FCU = model_manager.pattern_fcu
        Q_CCU = model_manager.pattern_ccu

        # ------ VARIABLES ------------------------------------------------------------------------
        lam = m.addVars({(v, r, p, s) for v in Vehicles for r in Routes[v] for p in Patterns[v] for s in
                         Scenarios},
                        vtype=GRB.CONTINUOUS, lb=0, ub=1, name="lam")

        x = m.addVars({(i, v, s) for i in Stations for v in Vehicles for s in Scenarios}, vtype=GRB.BINARY,
                      name="x")
        q_FCL = m.addVars({(v,s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_FCL")
        q_CCL = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_CCL")
        q_FCU = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_FCU")
        q_CCU = m.addVars({(v, s) for v in Vehicles for s in Scenarios}, vtype=GRB.INTEGER, lb=0, name="q_CCU")

        x_nac = m.addVars({(i,v) for i in Stations for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0, name="x_nac")
        q_FCL_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                              name="q_FCL_nac")
        q_CCL_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_CCL_nac")
        q_FCU_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_FCU_nac")
        q_CCU_nac = m.addVars({(v) for v in Vehicles}, vtype=GRB.CONTINUOUS, lb=0,
                             name="q_CCU_nac")

        # ------ CONSTRAINTS -----------------------------------------------------------------------
        for i in Swap_Stations:
            for v in Vehicles:
                for s in Scenarios:
                    lamsum = 0
                    for r in Routes[v]:
                        for p in Patterns[v]:
                            a = A[i][v][r]
                            lamsum += lam[(v, r, p, s)]
                    m.addConstr(a * lamsum == x[(i, v, s)])

        m.addConstr(x.sum('*', v, s) <= 1 for v in Vehicles for s in Scenarios)
        m.addConstr(x.sum(i, '*', s) <= 1 for i in Swap_Stations for s in Scenarios)

        for v in Vehicles:
            for s in Scenarios:
                sum_FCL = 0
                sum_CCL = 0
                sum_FCU = 0
                sum_CCU = 0
                for r in Routes[v]:
                    for p in Patterns[v]:
                        sum_FCL += lam[(v, r, p, s)] * Q_FCL[v][r][p]
                        sum_CCL += lam[(v, r, p, s)] * Q_CCL[v][r][p]
                        sum_FCU += lam[(v, r, p, s)] * Q_FCU[v][r][p]
                        sum_CCU += lam[(v, r, p, s)] * Q_CCU[v][r][p]
                m.addConstr(sum_FCL == q_FCL[v][s])
                m.addConstr(sum_CCL == q_CCU[v][s])
                m.addConstr(sum_FCU == q_FCU[v][s])
                m.addConstr(sum_CCU == q_CCU[v][s])

        # Non-anticipativity constraints
        m.addConstr(x_nac[(i, v)] == x[(i, v, s)] for i in Stations for v in Vehicles for s in Scenarios)
        m.addConstr(q_FCL_nac[v] == q_FCL[(v, s)] for v in Vehicles for s in Scenarios)
        m.addConstr(q_CCL_nac[v] == q_CCL[(v, s)] for v in Vehicles for s in Scenarios)
        m.addConstr(q_FCU_nac[v] == q_FCU[(v, s)] for v in Vehicles for s in Scenarios)
        m.addConstr(q_CCU_nac[v] == q_CCU[(v, s)] for v in Vehicles for s in Scenarios)

        # ------ OBJECTIVE -----------------------------------------------------------------------
        obj = 0
        for s in Scenarios:
            for v in Vehicles:
                for r in Routes[v]:
                    for p in Patterns[v]:
                        obj += C[r][p][s]*lam[(v, r, p, s)]

        m.setObjective(obj, GRB.MINIMIZE)

    except GurobiError:
            print(GurobiError.message)
