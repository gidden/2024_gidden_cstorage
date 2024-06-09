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

# %%
regions = ['R5ASIA', 'R5LAM', 'R5MAF', 'R5OECD90+EU', 'R5REF', 'World']

# %%
cdf = pd.read_csv(data_path / '102_ccs_data_r5_r10.csv', index_col=list(range(5)))
zdf = pd.read_csv(data_path / '102_netzero_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'-2': 'Net Zero GHGs', '-1': 'Net Zero CO2'})
limits = pd.read_csv(data_path / '101_Analysis_dataset_r5_r10.csv').set_index('Region')

# %%
hue_label = 'Threshold'

def make_limit(limits, region):
    row = limits.loc[region]
    return pd.DataFrame(
        {
            'value': row[['Pot_Final', 'Pot_ON_Final', 'Pot_OG']].values,
            'note': ['Global Preventative Limit', 'Global Onshore Limit', 'Global Limit with\nCurrent O&G Infrastructure']
        },
        index=pd.Index(['high', 'med', 'low'], name=hue_label),
    )

make_limit(limits, 'World')


# %%
# year that limit is reached after achieving net-zero CO2 emissions globally
def calc_time_to_limit(value, note, df):
    limit = value * 1e3
    nz_value = df.loc[ismatch(Variable='Cumulative Carbon Sequestration|CCS'), 'Net Zero CO2'].reset_index(level=['Variable'], drop=True)
    nz_rate= df.loc[ismatch(Variable='Carbon Sequestration|CCS'), 'Net Zero CO2'].reset_index(level=['Variable'], drop=True)
    return ((limit - nz_value) / nz_rate).pix.assign(**{hue_label: note})

nzdf = []
for region in regions:
    time_to_limit = pd.concat([calc_time_to_limit(row['value'], row['note'], zdf.loc[ismatch(Region=region)]) for i, row in make_limit(limits, region).iterrows()])
    nzdf.append(time_to_limit.to_frame(name='Years to Exceed at Net-zero CO2 Levels'))
nzdf = pd.concat(nzdf).reset_index(['Unit'], drop=True)

nzdf


# %%
# year of exceedence extrapolating 
def calc_time_to_limit(value, note, df):
    limit = value * 1e3
    nz_value = df.loc[ismatch(Variable='Cumulative Carbon Sequestration|CCS'), 'Net Zero CO2'].reset_index(level=['Variable'], drop=True)
    nz_rate= df.loc[ismatch(Variable='Carbon Sequestration|CCS'), 'Net Zero CO2'].reset_index(level=['Variable'], drop=True)
    return ((limit - nz_value) / nz_rate).pix.assign(**{hue_label: note})

def calc_year_exceedance(value, note, df):
    limit = value * 1e3
    ydf = df.loc[ismatch(Variable='Cumulative Carbon Sequestration|CCS')].copy() 
    ydf.columns = ydf.columns.astype(int)
    ydf[list(range(2101, 2301))] = np.nan
    extrap_ydf = ydf.interpolate(method="slinear", fill_value="extrapolate", limit_direction="both", axis=1)
    year_exceedance = (extrap_ydf > limit).idxmax(axis=1)
    year_exceedance[year_exceedance == 1990] = np.nan
    return year_exceedance.pix.assign(**{hue_label: note})


exdf = []
for region in regions:
    year_exceedance = pd.concat([calc_year_exceedance(row['value'], row['note'], df=cdf.loc[ismatch(Region=region)]) for i, row in make_limit(limits, region).iterrows()])
    exdf.append(year_exceedance.to_frame(name='Exceedance Year'))
exdf = pd.concat(exdf).reset_index(['Variable', 'Unit'], drop=True)

exdf


# %%
nzdf.join(exdf).to_csv(data_path / '103_exceedence_years.csv', index=True)

# %%
