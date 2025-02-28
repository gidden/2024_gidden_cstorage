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
data_path = Path('../data/packaged')
write_path = Path('../data/derived')

# %% [markdown]
# # Table 1: Storage by country

# %%
mdf = pd.read_csv(data_path / 'iso3c_region_mapping_20240602.csv')
mdf.head()

# %%
df = (
    pd.read_csv(data_path / 'Analysis_dataset_20240602.csv')
    .assign(
        Pot_Baseline=lambda _df: _df['Pot_OFF_Baseline'] + _df['Pot_ON_Baseline'],
        Pot_Final=lambda _df: _df['Pot_OFF_Final'] + _df['Pot_ON_Final'],
        Pot_OG=lambda _df: _df['Pot_OFF_OG'] + _df['Pot_ON_OG'],
    )
    .drop(['Absolute_Loss', 'Percentage_Loss'], axis=1)
)
df.head()

# %%
data = (
    pd.merge(mdf[['iso3c', 'name', 'r5_iamc']], df, left_on='iso3c', right_on='ISO')
    .dropna()
    .drop('ISO', axis=1)
    .rename(
        columns={
            'name': 'Country Name',
            'r5_iamc': 'IPCC 5-Region Name',
            'iso3c': 'Country ISO Code',
        }
    )
    .set_index(['Country ISO Code', 'Country Name', 'IPCC 5-Region Name'])
)
data.head()

# %%

names = {
    'Baseline': 'Technical Potential (Gt CO2)',
    'OG': 'Potential in Basins with Oil & Gas Infrastructure (Gt CO2)',
    'Final': 'Planetary Boundary Threshold (Gt CO2)'
}

table1 = []
for oname, nname in names.items():
    oldcols = [f'Pot_OFF_{oname}', f'Pot_ON_{oname}', f'Pot_{oname}']
    _data = data[oldcols]
    _data.columns = pd.MultiIndex.from_tuples((nname, kind) for kind in ['Offshore', 'Onshore', 'Total'])
    table1.append(_data)
table1 = pd.concat(table1, axis=1).round(1).sort_index(level='Country ISO Code')
table1.head()

# %%
table1.to_excel(write_path / '302_table1.xlsx', index=True)

# %%
