# Master_Heuristic

This repository implements a stack based simulator incorporating a heuristic to solve the
*Dynamic Stochastic Bicycle Rebalancing and Charging Problem* (DSBRCP). The simulator is event triggered. An event can
be triggered by a customer arrival at a station, a *bicycle trigger*, or a service vehicle arrival at a station,
a *vehicle trigger*. The test instance data is collected from *Oslo City Bike*. A valid [Google Cloud]
user with access to UIP's data is required.

The model is run from **main.py** where the following input-parameters should be set:
start_hour = the hour of the day to start the simulation
no_stations = the number of stations to include in the subset
branching = the branching factor in the first stage of the branching algorithm
subproblem_scenarios = the number of subproblem scenarios to include in each subproblem
simulation_time = the length of simulation in minutes

When running the simulator, a menu gives the user 7 possible analyses that can be conducted:
- w: weight analysis. Compares the performance of different weight sets.
- c: strategy comparison analysis. Compares the performance of 3 different strategies to solve the DSBRCP.
- r: runtime analysis. Compares the computational time with different input parameter configurations.
- fs: first step analysis. Compares the first step solutions using different input parameter configurations.
- v: vehicle analysis. Compares the performance when using different number of vehicles.
- charge: charging station analysis. Compares the effect of additional charging stations.
- vf: fleet analysis. Compares the effect of a non-homogeneous fleet.

The simulation output is saved in associated excel-files in the **Output** directory. A visualization of the simulation
can be seen by running **map_view.html** after completing the simulation.

[Google Cloud]: <https://cloud.google.com/bigquery>