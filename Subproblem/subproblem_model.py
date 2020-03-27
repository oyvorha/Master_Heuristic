from gurobipy import *
import time
import numpy as np


def run_model(parameters):

    try:
        m = Model("Heuristic")
        m.setParam('TimeLimit', 60 * 60)
        start_time = time.time()

        # ------ SETS -----------------------------------------------------------------------------
        Stations = parameters.stations
        Charging_stations = parameters.charging_stations
        Non_Charging_stations = parameters.non_charging_stations

        # ------ INDICES --------------------------------------------------------------------------
        o = 0
        b = parameters.depot_index

        # ------ PARAMETERS -----------------------------------------------------------------------
        T = parameters.visits
        Q_BV = parameters.Q_BV
        Q_CV = parameters.Q_CV
        Q_S = parameters.Q_S
        Q_B = parameters.Q_B
        Q_CCL = parameters.Q_CCL
        Q_FCL = parameters.Q_FCL
        Q_CCU = parameters.Q_CCU
        Q_FCU = parameters.Q_FCU
        L_BV = parameters.L_BV
        L_CV = parameters.L_CV
        L_FV = parameters.L_FV
        L_CS = parameters.L_CS
        L_FS = parameters.L_FS
        I_OC = parameters.I_OC
        I_IC = parameters.I_IC
        I_IF = parameters.I_IF

        V = parameters.V

        W_V = parameters.W_V

        # ------ VARIABLES ------------------------------------------------------------------------
        q_B = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="q_B")
        q_CCU = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="q_CCU")
        q_FCU = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="q_FCU")
        q_CCL = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="q_CCL")
        q_FCL = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="q_FCL")
        l_BV = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="l_BV")
        l_CV = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="l_CV")
        l_FV = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="l_FV")
        v_S = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="v_S")
        v_C = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="v_C")

        # ------ CONSTRAINTS -----------------------------------------------------------------------
        # Vehicle Loading Constraints
        m.addConstrs(q_B[i] <= l_BV[i] for i in Stations[1:])  # Exclude origin station
        m.addConstr(l_BV[o] == L_BV)
        m.addConstr(l_CV[o] == L_CV)
        m.addConstr(l_FV[o] == L_FV)
        if b:
            m.addConstrs(l_BV[b+1]-Q_BV == 0)
            m.addConstr(q_B[b] == 0)
        else:
            m.addConstrs(l_BV[i+1] - l_BV[i] + q_B[i] == 0 for i in Stations[:-1])
        m.addConstrs(l_CV[i+1] - l_CV[i] + q_CCU[i] - q_CCL[i] == 0 for i in Stations[:-1])
        m.addConstrs(l_FV[i+1] - l_FV[i] + q_FCU[i] - q_FCL[i] == 0 for i in Stations[:-1])
        m.addConstr(q_B[o] == Q_B)
        m.addConstr(q_FCL[o] == Q_FCL)
        m.addConstr(q_CCL[o] == Q_CCL)
        m.addConstr(q_FCU[o] == Q_FCU)
        m.addConstr(q_CCU[o] == Q_CCU)

        # Station loading constraints
        for i in Stations[1:]:
            if i != b:
                m.addConstr(q_B[i] <= L_FS[i] + q_FCU[i] - q_FCL[i])
                m.addConstr(q_FCL[i] <= L_FS[i])
                m.addConstr(q_CCL[i] <= L_CS[i])
                m.addConstr(q_FCU[i] + q_CCU[i] - q_FCL[i] - q_CCL[i] <= Q_S[i] - L_CS[i] - L_FS[i])

        # Violations
        # Situation 2
        m.addConstrs(L_CS[i] + q_B[i] + q_CCU[i] - q_CCL[i] + I_IC[i] - I_OC[i] + v_S[i] >= 0 for i in Stations[:-1])
        m.addConstrs(L_CS[i] + q_CCU[i] - q_CCL[i] + L_FS[i] + q_FCU[i] - q_FCL[i] + I_IC[i] + I_IF[i] - I_OC[i] +
                     v_S[i] - v_C[i] <= Q_S[i] for i in Stations[:-1])

        # ------ OBJECTIVE -----------------------------------------------------------------------
        m.setObjective(W_V * (np.sum(V) - v_C.sum('*') - v_S.sum('*')), GRB.MAXIMIZE)

        m.optimize()

        print(time.time() - start_time)
        for var in m.getVars():
            print(var.varName, var.x)

        return m

    except GurobiError:
            print(GurobiError.message)
