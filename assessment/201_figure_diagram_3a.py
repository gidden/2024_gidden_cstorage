# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: pyam
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pyam

from pathlib import Path
from pandas_indexing import ismatch

# %%
sns.set_style('whitegrid')

# %%
data_path = Path('../data/derived')
packaged_path = Path('../data/packaged')
figure_path = Path('../figures')

# %%
ldf = (
    pd.read_csv(data_path / '101_Analysis_dataset_global.csv')
    .set_index('index')
    ['World']
)

ldata = {
    'Main': {'World': {'Total': ldf.loc['Pot_Final'], 'Onshore': ldf.loc['Pot_ON_Final'], 'Offshore': ldf.loc['Pot_OFF_Final']}},
    'Oil and Gas': {'World': {'Total': 540}}
    }
all_limits = pd.DataFrame(ldata).T.rename_axis(index='Coverage', columns='Region').stack().apply(pd.Series)

hue_label = 'Threshold'
limits = pd.DataFrame([
    {hue_label: 'high', 'value':  all_limits.loc[ismatch(Coverage='Main', Region='World'), 'Total'][0], 'note': 'Global Preventative Limit',},
    {hue_label: 'med', 'value':  all_limits.loc[ismatch(Coverage='Main', Region='World'), 'Onshore'][0], 'note': 'Global Onshore Limit',},
    {hue_label: 'low', 'value':  all_limits.loc[ismatch(Coverage='Oil and Gas', Region='World'), 'Total'][0], 'note': 'Global Limit with\nCurrent O&G Infrastructure',},
]).set_index(hue_label)
limits

# %%
levels = ['Model', 'Scenario', 'Region', 'Variable', 'Unit']

df = (
    pyam.IamDataFrame(
        pd.read_excel(packaged_path / 'diagram_trajectories.xlsx').set_index(levels).pix.assign(Unit='Gt CO2/yr') * 1e-3
    )
    .interpolate(range(2015, 2101))
    )
df = pyam.concat([
    df,
    pyam.IamDataFrame(df.filter(variable='*Sequestration*').timeseries().cumsum(axis=1).pix.assign(variable='Cumulative Carbon Sequestration|CCS', unit='Gt CO2')),
])
df


# %%
def plot(var, nz=2055, limits=None, cumulative=False, fname=None, title=None, figsize=None, legend=None):
    fig, ax = plt.subplots(figsize=figsize)
    ax.axvline(nz, c='k', ls='-', alpha=0.5, label='Net-Zero CO2')
    if cumulative:
        ax.axhline(limits.loc['high', 'value'] / 2, xmin=0.475, xmax=1, c='r', ls=':', alpha=0.75, label='1/2 of Preventative Limit')
        ax.axhline(limits.loc['high', 'value'] / 4, xmin=0.475, xmax=1, c='orange', ls=':', alpha=0.75, label='1/4 of Preventative Limit')
    df.filter(variable=var).plot.line(linestyle='scenario', color='model', legend=legend, ax=ax, cmap='PuOr')
    if title is not None:
        ax.set_title('')
        fig.suptitle(title)
    ax.set_xlabel('')
    if fname is not None:
        fig.savefig(fname, transparent=True, bbox_inches='tight')
    return fig, ax


plot(var='Emissions*', title='Global CO2 Emissions', figsize=(4, 3), legend=False, fname=figure_path / 'diagram_emissions.pdf')
plot(var='Carbon Sequestration*', title='CO2 Injection Rates', figsize=(4, 3), legend=False, fname=figure_path / 'diagram_injection.pdf')
fig, ax = plot(var='Cumulative Carbon Sequestration*', title='Cumulative CO2 Storage', figsize=(4, 3), legend=False, cumulative=True, limits=limits, fname=figure_path / 'diagram_storage.pdf')

# %%
fig, ax = plot(var='Cumulative Carbon Sequestration*', title='Cumulative CO2 Storage', cumulative=True, limits=limits, legend={'loc': 'outside right', 'fontsize': 20}, figsize=(20, 5), fname=figure_path / 'diagram_storage_legend.pdf')
