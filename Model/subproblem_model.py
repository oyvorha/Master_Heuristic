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
        T_F = model_manager.time_to_last_visit
        Q_B = fixed.vehicle_bat_caps
        Q_C = fixed.vehicle_bike_caps
        Q_S = fixed.station_caps
        L_BV = model_manager.init_bat_load
        L_CV = model_manager.init_bat_bike_load
        L_FV = model_manager.init_flat_bike_load
        L_FS = model_manager.init_flat_station_load
        L_BS = model_manager.init_battery_station_load
        O = model_manager.ideal_states
        W_V = fixed.weight_violations
        W_D = fixed.weight_deviations
        W_R = fixed.weight_reward
        delta = model_manager.deltas
        gamma = model_manager.gammas

        Q_FCL = model_manager.flat_bike_load
        Q_CCL = model_manager.bat_bike_load
        Q_FCU = model_manager.flat_bike_offload
        Q_CCU = model_manager.bat_bike_offload

        # ------ VARIABLES ------------------------------------------------------------------------
        q_B = m.addVars({i for i in Swap_Stations}, vtype=GRB.INTEGER, lb=0, name="q_B")
        q_CCU = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="q_CCU")
        q_FCU = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="q_FCU")
        q_CCL = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="q_CCL")
        q_FCL = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="q_FCL")
        l_V = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="l_V")  # only swap?
        l_CC = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="l_CC")  # only swap?
        l_FC = m.addVars({i for i in Stations[:-1]}, vtype=GRB.INTEGER, lb=0, name="l_FC")  # only swap?
        s_B = m.addVars({i for i in Swap_Stations}, vtype=GRB.INTEGER, lb=0, name="s_B")
        s_F = m.addVars({i for i in Swap_Stations}, vtype=GRB.INTEGER, lb=0, name="s_F")
        v_S = m.addVars({i for i in Swap_Stations}, vtype=GRB.INTEGER, lb=0, name="v_S")
        d = m.addVars({i for i in Swap_Stations}, vtype=GRB.INTEGER, lb=0, name="d")

        # ------ CONSTRAINTS -----------------------------------------------------------------------
        # Vehicle Loading Constraints
        m.addConstrs(q_B[i] <= l_V[i] for i in Non_Charging_stations)
        m.addConstr(l_V[o] == L_BV)
        m.addConstr(l_CC[o] == L_CV)
        m.addConstr(l_FC[o] == L_BV)
        m.addConstrs(A[0][j]*(l_V[j]-Q_B) == 0 for j in Stations)
        m.addConstrs(A[i][j] * (l_V[j] - l_V[i] - q_B[i]) == 0 for i in Swap_Stations for j in Stations)
        m.addConstrs(A[i][j] * (l_CC[j] - l_CC[i] + q_CCU[i] - q_CCL[i]) == 0 for i in Stations[:-1] for j in Stations)
        m.addConstrs(A[i][j] * (l_FC[j] - l_FC[i] + q_FCU[i] - q_FCL[i]) == 0 for i in Stations[:-1] for j in Stations)
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
                m.addConstr(q_B[i] <= L_FS[i] - q_FCL[i])
                m.addConstr(q_FCL[i] <= L_FS[i])
                m.addConstr(q_B[i] - Q_B * A_sum_j[i] <= 0)
        for i in Swap_Stations:
            if i != o:
                m.addConstr(q_CCL[i] <= L_BS[i])
                m.addConstr(q_FCU[i] + q_CCU[i] - q_FCL[i] - q_CCL[i] <= Q_S[i] - L_BS[i] - L_FS[i])
                m.addConstr(q_FCU[i] + q_CCU[i] - Q_C[i] * A_sum_j[i] <= 0)
                m.addConstr(q_FCL[i] + q_CCL[i] - Q_C[i] * A_sum_j[i] <= 0)

        # Violations
        # Situation 2

        # Situation 3
        # m.addcontrs(v_SF * (1 - delta[i]) == 0 for i in Swap_Stations)
        # m.addcontrs(v_SF * delta[i] == v_S[i] for i in Swap_Stations)

        # ------ OBJECTIVE -----------------------------------------------------------------------
        # Deviations
        m.addConstrs(d[i] >= O[i] - s_B[i] for i in Swap_Stations)
        m.addConstrs(d[i] >= s_B[i] - O[i] for i in Swap_Stations)

        # m.setObjective()

    except GurobiError:
            print(GurobiError.message)
