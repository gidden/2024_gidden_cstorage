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

import pandas_indexing
import pyam

from pathlib import Path


# %%
def read_vars(fname, vars=[]):
    df = pd.read_csv(fname)
    df = df[df.Variable.isin(vars)]
    return df


# %%
data_path = Path('../data/packaged')
write_path = Path('../data/derived')
raw_path = Path('../data/raw')

# %%
fnames = [
    raw_path / 'AR6_Scenarios_Database_World_v1.1.csv',
    raw_path / 'AR6_Scenarios_Database_R5_regions_v1.1.csv',
    raw_path / 'AR6_Scenarios_Database_R10_regions_v1.1.csv',
    ]

data = [read_vars(fname, vars=['Carbon Sequestration|CCS', 'Carbon Sequestration|CCS|Fossil']) for fname in fnames]

# %%
levels = ['Model', 'Scenario']
gidx = data[0].set_index(levels).pix.unique(levels=levels)
r5idx = data[1].set_index(levels).pix.unique(levels=levels)
r10idx = data[2].set_index(levels).pix.unique(levels=levels)

# %%
gidx.difference(r5idx).unique('Model')

# %%
check = data[0].copy()
check['Has R5'] = True
check.loc[check['Model'].isin(gidx.difference(r5idx).unique('Model')), 'Has R5'] = False
sns.violinplot(data=check, y='Variable', x='2100', hue='Has R5', inner="point")
check['Has R5'].value_counts()

# %%
r5idx.difference(r10idx).unique('Model')

# %%
check = data[1].copy().set_index(['Model', 'Scenario', 'Region', 'Variable', 'Unit']).pix.aggregate(Region={'World': data[1]['Region'].unique()}, mode='return').reset_index()
check['Has R10'] = True
check.loc[check['Model'].isin(r5idx.difference(r10idx).unique('Model')), 'Has R10'] = False
sns.violinplot(data=check, y='Variable', x='2100', hue='Has R10', inner="point")
check['Has R10'].value_counts()

# %% [markdown]
# # Now we interpolate, add cumulative variables, and set values at net-zero

# %%
df = pyam.IamDataFrame(pd.concat(data)).interpolate(range(2010, 2101))

# %%
df.filter(region='World', scenario='EMF33_Med2C_cost100').plot.line(color='variable')


# %%
def make_cumulative_df(df, vold, vnew, offset=False):
    y1 = offset or 2010
    y2 = 2100
    data = df.filter(variable=vold).interpolate(range(y1, y2 + 1))
    if offset:
        data = data.offset(year=y1) # NB this fails if there is no value in the year
    pddata = (
        data
        .filter(year=range(y1, y2 + 1))
        .rename(variable={vold: vnew})
        .timeseries()
    )
    ret = pyam.IamDataFrame(pddata.cumsum(axis=1))
    ret.set_meta(data.meta)
    return ret


# %%
cdf = pyam.concat([
    make_cumulative_df(df, vold='Carbon Sequestration|CCS', vnew='Cumulative Carbon Sequestration|CCS'),
    make_cumulative_df(df, vold='Carbon Sequestration|CCS|Fossil', vnew='Cumulative Carbon Sequestration|CCS|Fossil'),
])

# %%
data = pyam.concat([df, cdf])
data.to_csv(write_path / '102_ccs_data_r5_r10.csv')


# %%
data.load_meta(raw_path / 'AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx')


# %%
def value_at_net_zero(row, nz):
    year = nz.loc[row.name[0], row.name[1]]
    return row[year] if np.isfinite(year) else np.nan

nz = data.meta['Year of netzero CO2 emissions (Harm-Infilled) Table SPM2']
nz_co2 = data.timeseries().apply(value_at_net_zero, args=(nz,), axis=1).pix.assign(year=-1) # NB: net-zero co2 year is set to -1

nz = data.meta['Year of netzero GHG emissions (Harm-Infilled) Table SPM2']
nz_ghg = data.timeseries().apply(value_at_net_zero, args=(nz,), axis=1).pix.assign(year=-2) # NB: net-zero ghg year is set to -2

pyam.IamDataFrame(pd.concat([nz_co2, nz_ghg])).to_csv(write_path / '102_netzero_ccs_data_r5_r10.csv')


# %% [markdown]
# ## Quick Check

# %%
data = pyam.IamDataFrame(write_path / '102_netzero_ccs_data_r5_r10.csv')
data.load_meta(raw_path / 'AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx')

ax = (
    data
    .filter(variable='Cumulative Carbon Sequestration|CCS', year=[-1, -2], region='World')
    .filter(Category='C*')
    .convert_unit('Mt CO2/yr', 'Gt CO2', factor=1e-3)
    .plot.box(x="year", by="Category", legend=True)
)

# %%
