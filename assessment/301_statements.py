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
from pandas_indexing import ismatch, isin

# %%
data_path = Path('../data/derived')
raw_path = Path('../data/raw')

# %%
limits = pd.read_csv(data_path / '101_global_limits.csv', index_col=0)
limits

# %%

cdf = pd.read_csv(data_path / '102_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'2100': 'End of Century'})
zdf = pd.read_csv(data_path / '102_netzero_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'-2': 'Net Zero GHGs', '-1': 'Net Zero CO2'})
mdf = pd.read_excel(raw_path / 'AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx', sheet_name='meta', index_col=list(range(2)))

# %%
df = (
    pd.concat((cdf['End of Century'], zdf[['Net Zero GHGs', 'Net Zero CO2']]), axis=1)
    .loc[ismatch(Region='World')]
    .pix.assign(Category=mdf['Category'])
    .loc[isin(Category=['C1', 'C2', 'C3', 'C4'])]
    .pix.project(['Variable', 'Category'])
)
df.head()

# %% [markdown]
# # For the statement
#
# > While all scenarios limiting warming below 2°C deploy some level of CCS, some scenarios that intend to strongly revert global warming after weak emission reductions over the next decades utilize up to 2000 Gt of storage by the end of the century.

# %%
data = (    
    cdf['End of Century'].loc[isin(Region='World')].unstack('Variable')
    .join(mdf, on=['Model', 'Scenario'])
    .pix.assign(Category=mdf['Category'])
    .loc[isin(Category=['C1', 'C2', 'C3', 'C4'])]
    .assign(drawdown=lambda df: df['Median peak warming (MAGICCv7.5.3)'] - df['Median warming in 2100 (MAGICCv7.5.3)'])
    )
sns.relplot(data=data, x='drawdown', y='Cumulative Carbon Sequestration|CCS', hue='Category')
data.loc[isin(Category='C2')].plot.scatter(x='drawdown', y='Cumulative Carbon Sequestration|CCS')


# %% [markdown]
# # For the statement
#
# > Nearly all scenarios assessed by the IPCC stay within a 50% margin or greater of our assessed planetary boundary when net-zero CO2 emissions is reached (Figure 3b). Even so, scenarios limiting warming to 1.5C with no or limited overshoot sequester 8.7 [5.9-13] Gt CO2yr-1 when reaching net-zero CO2 emissions around 2050-2055. This represents a 175 fold increase from today’s levels and an industrial capacity on par with current global crude oil production (59). Carbon injection rates at net-zero CO2 systematically increase with decreasing policy stringency, with a quarter of 2C (>50%) scenarios injecting more than 20 Gt CO2yr-1.

# %%
df.head()

# %%
df.groupby(level=['Variable', 'Category']).describe([0.05, 0.25, 0.5, 0.75, 0.95])['Net Zero CO2']

# %%
# compared to today
8661.657800 / 49

# %% [markdown]
# # For the statement
#
# > In 2100, carbon storage activity is continuing to grow past this limit, with 1.5C and 2C scenarios storing on average 15 [11, 18] Gt CO2yr-1. 

# %%
df.groupby(level=['Variable']).describe([0.05, 0.25, 0.5, 0.75, 0.95])['End of Century']

# %%
df.groupby(level=['Variable', 'Category']).describe([0.05, 0.25, 0.5, 0.75, 0.95])['End of Century']

# %% [markdown]
# # Simple C-budget calcs

# %%
main_limit = limits.loc['high', 'value']
tcre_p50 = 0.45 / 1000 # C per 1000 GtCO2
tcre_p66 = 0.27 / 1000 # C per 1000 GtCO2
main_limit

# %%
tcre_p50 * main_limit

# %%
tcre_p66 * main_limit
