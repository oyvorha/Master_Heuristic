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
        Charging_stations = Stations[5:-1]
        Non_Charging_stations = Stations[1:4]
        Swap_Stations = Stations[1:-1]

        # ------ INDICES --------------------------------------------------------------------------
        o = model_manager.starting_index

        # ------ PARAMETERS -----------------------------------------------------------------------
        A = model_manager.matrix
        time_horizon = fixed.time_horizon
        T = model_manager.visits
        Q_BV = fixed.vehicle_bat_caps
        Q_CV = fixed.vehicle_bike_caps
        Q_S = fixed.station_caps
        Q_B = model_manager.pattern_b
        Q_CCL = model_manager.pattern_ccl
        Q_FCL = model_manager.pattern_fcl
        Q_CCU = model_manager.pattern_ccu
        Q_FCU = model_manager.pattern_fcu
        L_BV = model_manager.init_bat_load
        L_CV = model_manager.init_bat_bike_load
        L_FV = model_manager.init_flat_bike_load
        L_CS = model_manager.init_battery_station_load
        L_FS = model_manager.init_flat_station_load
        I_OC = model_manager.demand
        I_IC = model_manager.incoming_charged_bikes
        I_IF = model_manager.incoming_flat_bikes

        V_TbarS = model_manager.starvation_tbar
        V_TS = model_manager.starvation_t
        V_TbarC = model_manager.congestion_tbar
        V_TC = model_manager.congestion_t

        W_V = fixed.weight_violations
        W_D = fixed.weight_deviations
        W_R = fixed.weight_reward

        # ------ VARIABLES ------------------------------------------------------------------------
        q_B = m.addVars({i for i in Swap_Stations}, vtype=GRB.CONTINUOUS, lb=0, name="q_B")
        q_CCU = m.addVars({i for i in Stations[:-1]}, vtype=GRB.CONTINUOUS, lb=0, name="q_CCU")
        q_FCU = m.addVars({i for i in Stations[:-1]}, vtype=GRB.CONTINUOUS, lb=0, name="q_FCU")
        q_CCL = m.addVars({i for i in Stations[:-1]}, vtype=GRB.CONTINUOUS, lb=0, name="q_CCL")
        q_FCL = m.addVars({i for i in Stations[:-1]}, vtype=GRB.CONTINUOUS, lb=0, name="q_FCL")
        l_BV = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="l_BV")
        l_CV = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="l_CV")
        l_FV = m.addVars({i for i in Stations}, vtype=GRB.CONTINUOUS, lb=0, name="l_FV")
        v_S = m.addVars({i for i in Swap_Stations}, vtype=GRB.CONTINUOUS, lb=0, name="v_S")
        v_C = m.addVars({i for i in Swap_Stations}, vtype=GRB.CONTINUOUS, lb=0, name="v_C")
        d = m.addVars({i for i in Swap_Stations}, vtype=GRB.CONTINUOUS, lb=0, name="d")

        # ------ CONSTRAINTS -----------------------------------------------------------------------
        # Vehicle Loading Constraints
        m.addConstrs(q_B[i] <= l_BV[i] for i in Non_Charging_stations) # Exclude origin station
        m.addConstr(l_BV[o] == L_BV)
        m.addConstr(l_CV[o] == L_CV)
        m.addConstr(l_FV[o] == L_FV)
        m.addConstrs(A[0][j]*(l_BV[j]-Q_BV) == 0 for j in Stations)
        m.addConstrs(A[i][j] * (l_BV[j] - l_BV[i] + q_B[i]) == 0 for i in Swap_Stations for j in Stations)
        m.addConstrs(A[i][j] * (l_CV[j] - l_CV[i] + q_CCU[i] - q_CCL[i]) == 0 for i in Stations[:-1] for j in Stations)
        m.addConstrs(A[i][j] * (l_FV[j] - l_FV[i] + q_FCU[i] - q_FCL[i]) == 0 for i in Stations[:-1] for j in Stations)
        m.addConstr(q_CCL[0] - q_CCU[0] == 0)
        m.addConstr(q_FCL[0] - q_FCU[0] == 0)
        m.addConstr(q_B[o] == Q_B)
        m.addConstr(q_FCL[o] == Q_FCL)
        m.addConstr(q_CCL[o] == Q_CCL)
        m.addConstr(q_FCU[o] == Q_FCU)
        m.addConstr(q_CCU[o] == Q_CCU)

        # Station loading constraints
        A_sum_j = np.sum(A, axis=0)
        for i in Non_Charging_stations:
            if i != o:
                m.addConstr(q_B[i] <= L_FS[i] + q_FCU[i]- q_FCL[i])
                m.addConstr(q_FCL[i] <= L_FS[i])
                m.addConstr(q_[i] - Q_S * A_sum_j[i] <= 0)
        for i in Swap_Stations:
            if i != o:
                m.addConstr(q_CCL[i] <= L_CS[i])
                m.addConstr(q_FCU[i] + q_CCU[i] - q_FCL[i] - q_CCL[i] <= Q_S[i] - L_CS[i] - L_FS[i])
                m.addConstr(q_FCU[i] + q_CCU[i] - Q_S[i] * A_sum_j[i] <= 0)
                m.addConstr(q_FCL[i] + q_CCL[i] - Q_S[i] * A_sum_j[i] <= 0)

        # Violations
        # Situation 2
        m.addConstr(L_CS[i] + q_B[i] + q_CCU[i] - q_CCL[i] + I_IC[i] - I_OC[i] + v_S[i] >= 0 for i in Swap_Stations)
        m.addConstr(L_CS[i] + q_CCU[i] - q_CCL[i] + L_FS[i] + q_FCU[i] - q_FCL[i] + I_IC[i] + I_IF[i] - I_OC[i] +
                    v_S[i] - v_C[i] <= Q_S[i] for i in Swap_Stations)

        # ------ OBJECTIVE -----------------------------------------------------------------------
        m.setObjective(W_V * (v_S.sum('*') + V_TbarS.sum('*') + V_TS.sum('*') + v_C.sum('*') + V_TbarC.sum('*') +
                              V_TC.sum('*')), GRB.MINIMIZE)

        print(time.time() - start_time)
        return m

    except GurobiError:
            print(GurobiError.message)
