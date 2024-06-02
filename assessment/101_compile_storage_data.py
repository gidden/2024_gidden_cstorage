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

# %% [markdown]
# # Overview
#
# This notebook aggregates country-level carbon storage data into IPCC region definitions

# %%
import pandas as pd
from pandas_indexing import ismatch

from pathlib import Path

# %%
data_path = Path('../data/packaged')
write_path = Path('../data/derived')


# %%
def cols_to_dict(df, col1, col2):
    keys = df[col1].unique()
    df = df.set_index(col1)
    return {key: df[col2][key].to_list() for key in keys}

mdf = pd.read_csv(data_path / 'iso3c_region_mapping_20240319_highlighted.csv')
r5_mapping = cols_to_dict(mdf.dropna(subset='r5_iamc'), 'r5_iamc', 'iso3c')
r10_mapping = cols_to_dict(mdf.dropna(subset='r10_iamc'), 'r10_iamc', 'iso3c')
w_mapping = {'World': mdf.iso3c.unique()}

mdf.head()

# %%
df = (
    pd.read_csv(data_path / 'Analysis_dataset.csv', index_col='ISO')
    .assign(
        Pot_Baseline=lambda _df: _df['Pot_OFF_Baseline'] + _df['Pot_ON_Baseline'],
        Pot_Final=lambda _df: _df['Pot_OFF_Final'] + _df['Pot_ON_Final'],
    )
    .drop(['Absolute_Loss', 'Percentage_Loss'], axis=1)
)
df.head()


# %%
def aggregate(df, mapping):
    df = df.pix.aggregate(ISO=mapping, mode='return')
    df['Percentage lost (net vs gross)'] = 1 - df['Pot_Final'] / df['Pot_Baseline']
    return df.rename_axis(index={'ISO': 'Region'})

data = pd.concat([
    aggregate(df, r5_mapping),
    aggregate(df, r10_mapping),
    aggregate(df, w_mapping),
])

data

# %%
data.to_csv(write_path / '101_Analysis_dataset_r5_r10.csv', index=True)
