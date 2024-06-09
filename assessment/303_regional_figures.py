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

# %% [markdown]
# # Utilities

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

limits = pd.read_csv(data_path / '101_Analysis_dataset_r5_r10.csv').set_index('Region')
make_limit(limits, 'World')

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


# %% [markdown]
# # Dist fig

# %%
def add_spans(ax, limits, orient='h'):
    span = ax.axvspan if orient == 'h' else ax.axhspan
    get = lambda l: limits[l] * 1e3
    if get('Pot_ON_Final') > get('Pot_OG'):
        span(0, get('Pot_OG'), color='plum', alpha=0.25, zorder=0)
        span(get('Pot_OG'), get('Pot_ON_Final'), color='orange', alpha=0.25, zorder=0)
        span(get('Pot_ON_Final'), get('Pot_Final'), color='orangered', alpha=0.25, zorder=0)
    else:
        span(0, get('Pot_ON_Final'), color='plum', alpha=0.25, zorder=0)
        span(get('Pot_ON_Final'), get('Pot_Final'), color='orangered', alpha=0.25, zorder=0)
    xmax = ax.get_xlim()[1] if orient == 'h' else ax.get_ylim()[1]
    if xmax > get('Pot_Final'):
        span(get('Pot_Final'), xmax, color='black', alpha=0.25, zorder=0)


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

add_label_mapping(data, drop=True)

cstor_data = data.melt(id_vars=['Category', cat_label], value_vars=['Net Zero CO2', 'End of Century'], ignore_index=False)
cstor_data = cstor_data.where(mdata.Category.isin(label_mapping.keys()))
cstor_data.head()


# %%
def plot_cstorage_dist(data, limits, region, ax=None):
    sns.set_style("whitegrid")
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 12))

    palette = {
        'Net Zero CO2': 'thistle', 
        'End of Century': 'mediumpurple',
    }

    _data = data.loc[ismatch(Region=region, Variable='Cumulative Carbon Sequestration|CCS')].reset_index(drop=True)
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
    ax.set_title(f'Carbon Storage Utilized in {region}', fontsize=16)

    return ax


# %%
plot_cstorage_dist(cstor_data, limits, 'World')

# %% [markdown]
# # Exceedence Figs

# %%
exdf = (
    pd.read_csv(data_path / '103_exceedence_years.csv', index_col=list(range(4)))
    .join(mdf['Category'], on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
add_label_mapping(exdf, drop=True)
exdf = exdf.reset_index(['Model', 'Scenario', 'Threshold'], drop=False)
exdf


# %%
def plot_nz_exceedence(data, x, legend=None, ax=None):
    if ax is None:
        FIGSIZE = (10, 3)
        sns.set_style("whitegrid")
        fig, ax = plt.subplots(figsize=FIGSIZE)

    colors = {
        'low': 'plum',
        'med': 'orange',
        'high': 'orangered',
    }

    sns.boxplot(
            data=data,
            x=x,
            y=cat_label,
            hue=hue_label,
            legend=legend,
            order=label_mapping.values(),
            showfliers=False,
            ax=ax,
            palette=[colors['high'], colors['med'], colors['low']],
            ).set(ylabel='', xlabel='', title=x)
    
    return ax


# %%
plot_nz_exceedence(exdf.loc['World'].reset_index(), legend=True, x='Years to Exceed at Net-zero CO2 Levels')

# %%
plot_nz_exceedence(exdf.loc['World'].reset_index(), x='Exceedance Year')

# %% [markdown]
# # Figure 3b-d

# %%
region = 'World'
sns.set_style("whitegrid")

fig, ax = plt.subplots(figsize=(7, 12))
plot_cstorage_dist(cstor_data, limits, region, ax=ax)
fig.savefig(figure_path / 'figure_3b.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig(figure_path / 'figure_3b.png', bbox_inches='tight', dpi=1e3)

fig, ax = plt.subplots(figsize=(10, 3))
plot_nz_exceedence(exdf.loc[region].reset_index(), legend=True, x='Years to Exceed at Net-zero CO2 Levels', ax=ax)
fig.savefig(figure_path / 'figure_3c.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig(figure_path / 'figure_3c.png', bbox_inches='tight', dpi=1e3)

fig, ax = plt.subplots(figsize=(10, 3))
plot_nz_exceedence(exdf.loc[region].reset_index(), legend=False, x='Exceedance Year', ax=ax)
fig.savefig(figure_path / 'figure_3d.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig(figure_path / 'figure_3d.png', bbox_inches='tight', dpi=1e3)


# %% [markdown]
# # SI Figures

# %%
def full_fig(region):
  fig, axs = plt.subplots(3, 1, figsize=(10, 15), height_ratios=[4, 1, 1])

  plot_cstorage_dist(cstor_data, limits, region, ax=axs[0])
  plot_nz_exceedence(exdf.loc[region].reset_index(), legend=True, x='Years to Exceed at Net-zero CO2 Levels', ax=axs[1])
  plot_nz_exceedence(exdf.loc[region].reset_index(), x='Exceedance Year', ax=axs[2])

  for i, label in enumerate(('A', 'B', 'C')):
      axs[i].text(-0.1, 1.15, label, transform=axs[i].transAxes,
        fontsize=16, fontweight='bold', va='top', ha='right')
  return fig


# %%
fig = full_fig(region='World')

# %%
regions = ['R5ASIA', 'R5LAM', 'R5MAF', 'R5OECD90+EU', 'R5REF']
for region in regions:
    fig = full_fig(region)
    fig.savefig(figure_path / f'figure_si_like3_{region}.pdf', bbox_inches='tight', dpi=1e3)
    fig.savefig(figure_path / f'figure_si_like3_{region}.png', bbox_inches='tight', dpi=1e3)

# %%
