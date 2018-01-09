# -*- coding: utf-8 -*-
"""
General description:
---------------------
Example that illustrates how to use custom component `GenericCHP` can be used.
In this case it is used to model a motoric chp.

Installation requirements:
---------------------------
This example requires the latest version of oemof. Install by:

    pip install oemof

"""

import pandas as pd
import oemof.solph as solph
from oemof.network import Node
from oemof.outputlib import processing, views
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# read sequence data
file_name = 'generic_chp'
data = pd.read_csv(file_name + '.csv', sep=",")

# select periods
periods = len(data)-1

# create an energy system
idx = pd.date_range('1/1/2017', periods=periods, freq='H')
es = solph.EnergySystem(timeindex=idx)
Node.registry = es

# resources
bgas = solph.Bus(label='bgas')

rgas = solph.Source(label='rgas', outputs={bgas: solph.Flow()})

# heat
bth = solph.Bus(label='bth')

# dummy source at high costs that serves the residual load
source_th = solph.Source(label='source_th',
                         outputs={bth: solph.Flow(variable_costs=1000)})

demand_th = solph.Sink(label='demand_th', inputs={bth: solph.Flow(fixed=True,
                       actual_value=data['demand_th'], nominal_value=200)})

# power
bel = solph.Bus(label='bel')

demand_el = solph.Sink(label='demand_el', inputs={bel: solph.Flow(
                       variable_costs=data['price_el'])})

# motoric chp
mchp = solph.components.GenericCHP(
    label='motoric_chp',
    fuel_input={bgas: solph.Flow(
        H_L_FG_share_max=[0.18 for p in range(0, periods)],
        H_L_FG_share_min=[0.41 for p in range(0, periods)])},
    electrical_output={bel: solph.Flow(
        P_max_woDH=[200 for p in range(0, periods)],
        P_min_woDH=[100 for p in range(0, periods)],
        Eta_el_max_woDH=[0.44 for p in range(0, periods)],
        Eta_el_min_woDH=[0.40 for p in range(0, periods)])},
    heat_output={bth: solph.Flow(
        Q_CW_min=[0 for p in range(0, periods)])},
    Beta=[0 for p in range(0, periods)],
    fixed_costs=0, back_pressure=False)

# create an optimization problem and solve it
om = solph.Model(es)

# debugging
# om.write('generic_chp.lp', io_options={'symbolic_solver_labels': True})

# solve model
om.solve(solver='cbc', solve_kwargs={'tee': True})

# create result object
results = processing.results(om)

# store as csv
# data = results[(mchp,)]['sequences'].to_csv('results_ccet_' + file_name)

# plot data
if plt is not None:
    # plot PQ diagram from component results
    data = results[(mchp, None)]['sequences']
    ax = data.plot(kind='scatter', x='Q', y='P', grid=True)
    ax.set_xlabel('Q (MW)')
    ax.set_ylabel('P (MW)')
    plt.show()

    # plot thermal bus
    data = views.node(results, 'bth')['sequences']
    ax = data.plot(kind='line', drawstyle='steps-post', grid=True)
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Q (MW)')
    plt.show()
