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

mdf = pd.read_csv(data_path / 'iso3c_region_mapping_20240602.csv')
r5_mapping = cols_to_dict(mdf.dropna(subset='r5_iamc'), 'r5_iamc', 'iso3c')
r10_mapping = cols_to_dict(mdf.dropna(subset='r10_iamc'), 'r10_iamc', 'iso3c')
w_mapping = {'World': mdf.iso3c.unique()}

mdf.head()

# %%
df = (
    pd.read_csv(data_path / 'Analysis_dataset_20240602.csv', index_col='ISO')
    .assign(
        Pot_Baseline=lambda _df: _df['Pot_OFF_Baseline'] + _df['Pot_ON_Baseline'],
        Pot_Final=lambda _df: _df['Pot_OFF_Final'] + _df['Pot_ON_Final'],
        Pot_OG=lambda _df: _df['Pot_OFF_OG'] + _df['Pot_ON_OG'],
    )
    .drop(['Absolute_Loss', 'Percentage_Loss'], axis=1)
)
df.head()


# %%

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
# we have to replace non-oil and gas with world values which include antartica and non-EEZ areas
wdf = pd.read_excel(data_path / 'Sensitivity_table_20240602.xlsx', sheet_name='data')
wdf

# %%
data.loc['World', ['Pot_ON_Baseline',  'Pot_OFF_Baseline', 'Pot_Baseline']] = wdf.iloc[0][['Onshore', 'Offshore', 'Total']].values
data.loc['World', ['Pot_ON_Final',  'Pot_OFF_Final', 'Pot_Final']] = wdf.iloc[-1][['Onshore', 'Offshore', 'Total']].values
data.loc['World', 'Percentage lost (net vs gross)'] = 1 - data.loc['World', 'Pot_Final'] / data.loc['World', 'Pot_Baseline']
data

# %%
data.to_csv(write_path / '101_Analysis_dataset_r5_r10.csv', index=True)

# %% [markdown]
# # Limits file used in subsequent analysis

# %%
globaldf = df.sum().reset_index(name='World')
globaldf.to_csv(write_path / '101_Analysis_dataset_global.csv', index=False)

# %%
globaldf

# %%
ldf = (
    pd.read_csv(write_path / '101_Analysis_dataset_global.csv')
    .set_index('index')
    ['World']
)

ldata = {
    'Main': {'World': {'Total': ldf.loc['Pot_Final'], 'Onshore': ldf.loc['Pot_ON_Final'], 'Offshore': ldf.loc['Pot_OFF_Final']}},
    'Oil and Gas': {'World': {'Total': ldf.loc['Pot_OG'], 'Onshore': ldf.loc['Pot_ON_OG'], 'Offshore': ldf.loc['Pot_OFF_OG']}},
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
limits.to_csv(write_path / '101_global_limits.csv', index=True)
