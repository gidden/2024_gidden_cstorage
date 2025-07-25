# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: scen
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
data_path = Path('../data/raw')
write_path = Path('../data/derived')

# %%
df = pd.read_excel(data_path / 'gidden_et_al_2025_supplemental_data.xlsx', sheet_name='S5', skiprows=range(2))
cols = ['ISO', 'NAME', 'Region', 'Pot_OFF_Baseline', 'Pot_ON_Baseline', 'Pot_Baseline',	'Pot_OFF_Final', 'Pot_ON_Final', 'Pot_Final', 'Pot_OFF_OG', 'Pot_ON_OG', 'Pot_OG']
df.columns = cols
df = df.drop([193, 194, 229]) # get rid of pre-calculated totals
df.iloc[-1, 2] = 'World' # manually set world
df

# %%
df.to_csv(write_path / '101_Analysis_dataset_iso.csv', index=True)
df = df.drop(['ISO', 'NAME'], axis=1).groupby('Region').sum()
df.to_csv(write_path / '101_Analysis_dataset_r5_r10.csv', index=True)

# %% [markdown]
# # Limits file used in subsequent analysis

# %%
ldf = df.loc['World']

ldata = {
    'Main': {'World': {'Total': ldf.loc['Pot_Final'], 'Onshore': ldf.loc['Pot_ON_Final'], 'Offshore': ldf.loc['Pot_OFF_Final']}},
    'Oil and Gas': {'World': {'Total': ldf.loc['Pot_OG'], 'Onshore': ldf.loc['Pot_ON_OG'], 'Offshore': ldf.loc['Pot_OFF_OG']}},
    }
all_limits = pd.DataFrame(ldata).T.rename_axis(index='Coverage', columns='Region').stack().apply(pd.Series)

hue_label = 'Threshold'
limits = pd.DataFrame([
    {hue_label: 'high', 'value':  all_limits.loc[ismatch(Coverage='Main', Region='World'), 'Total'][0], 'note': 'Global Prudent Limit',},
    {hue_label: 'med', 'value':  all_limits.loc[ismatch(Coverage='Main', Region='World'), 'Onshore'][0], 'note': 'Global Onshore Limit',},
    {hue_label: 'low', 'value':  all_limits.loc[ismatch(Coverage='Oil and Gas', Region='World'), 'Total'][0], 'note': 'Global Limit with\nCurrent O&G Infrastructure',},
]).set_index(hue_label)
limits

# %%
limits.to_csv(write_path / '101_global_limits.csv', index=True)
