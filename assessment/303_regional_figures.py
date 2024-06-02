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
figure_path = Path('../figures')

# %%
limits = pd.read_csv(data_path / '101_Analysis_dataset_r5_r10.csv').set_index('Region')
limits


# %%
cdf = pd.read_csv(data_path / '102_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'2100': 'End of Century'})
zdf = pd.read_csv(data_path / '102_netzero_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'-2': 'Net Zero GHGs', '-1': 'Net Zero CO2'})
mdf = pd.read_excel(raw_path / 'AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx', sheet_name='meta', index_col=list(range(2)))

# %%
data = (
    pd.concat((cdf['End of Century'], zdf[['Net Zero GHGs', 'Net Zero CO2']]), axis=1)
    .join(mdf, on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
data.head()

# %%
cat_label = 'Category_label'
label_mapping = {
    'C1': '1.5°C (>33%,\n>50% in 2100)',
    'C2': '1.5°C (<33%,\n>50% in 2100)',
    'C3': '2°C (>67%)',
    'C4': '2°C (>50%)',
#    'C5': '2.5°C (>50%)',
}

def add_label_mapping(df, drop=False):
    df[cat_label] = df['Category'].replace(label_mapping)
    if drop:
        df.drop(df[~df['Category'].isin(label_mapping.keys())].index, inplace=True)

add_label_mapping(data, drop=True)


# %%
def add_spans(ax, limits, orient='h'):
    func = ax.axvspan if orient == 'h' else ax.axhspan
    get = lambda l: limits[l] * 1e3
    if get('Pot_ON_Final') > get('Pot_OG'):
        func(0, get('Pot_OG'), color='plum', alpha=0.25, zorder=0)
        func(get('Pot_OG'), get('Pot_ON_Final'), color='orange', alpha=0.25, zorder=0)
        func(get('Pot_ON_Final'), get('Pot_Final'), color='orangered', alpha=0.25, zorder=0)
    else:
        func(0, get('Pot_ON_Final'), color='plum', alpha=0.25, zorder=0)
        func(get('Pot_ON_Final'), get('Pot_Final'), color='orangered', alpha=0.25, zorder=0)
    xmax = ax.get_xlim()[1] if orient == 'h' else ax.get_ylim()[1]
    if xmax > get('Pot_Final'):
        func(get('Pot_Final'), xmax, color='black', alpha=0.25, zorder=0)


# %%
mdata = data.melt(id_vars=['Category', cat_label], value_vars=['Net Zero CO2', 'End of Century'], ignore_index=False)
mdata = mdata.where(mdata.Category.isin(label_mapping.keys()))
mdata.head()


# %%
def plot(mdata, region):
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(7, 12))

    palette = {
        'Net Zero CO2': 'thistle', 
        'End of Century': 'mediumpurple',
    }

    _data = mdata.loc[ismatch(Region=region, Variable='Cumulative Carbon Sequestration|CCS')].reset_index(drop=True)
    sns.violinplot(
            data=_data,
            y='value',
            hue='variable',
            x=cat_label,
            order=label_mapping.values(),
            inner='quart',
            split=True,
            cut=0,
            ax=ax,
            palette=palette,
            )

    add_spans(ax, limits.loc[region], orient='v')
    ax.legend(loc='upper right')
    ax.set_ylabel('Cumulative Stored CO2 (Mt)')
    ax.set_xlabel('')
    ax.set_title(f'Storage in {region}')

    fig.savefig(figure_path / f'303_figure_si_storage_{region}.pdf', bbox_inches='tight', dpi=1e3)
    fig.savefig(figure_path / f'303_figure_si_storage_{region}.png', bbox_inches='tight', dpi=1e3)


# %%
for region in ['R5ASIA', 'R5LAM', 'R5MAF', 'R5OECD90+EU', 'R5REF']:
    plot(mdata, region)

# %%

# %%
