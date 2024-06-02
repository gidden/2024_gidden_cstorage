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
data_path = Path('../processed_data/')
ar6_path = Path('../raw_data/')

# %%
cdf = pd.read_csv(data_path / '../processed_data/102_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'2100': 'End of Century'})
zdf = pd.read_csv(data_path / '102_netzero_ccs_data_r5_r10.csv', index_col=list(range(5))).rename(columns={'-2': 'Net Zero GHGs', '-1': 'Net Zero CO2'})
mdf = pd.read_excel(ar6_path / 'AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx', sheet_name='meta', index_col=list(range(2)))

# %%
# read using Sid's data
# limits = pd.read_csv(data_path / '101_D2_compiled_r5_r10.csv', index_col=0)


ldata = {
    'Main': {'World': {'Total': 1595, 'Onshore': 1121, 'Offshore': 474}},
    'Oil and Gas': {'World': {'Total': 903}}
    }
all_limits = pd.DataFrame(ldata).T.rename_axis(index='Coverage', columns='Region').stack().apply(pd.Series)

hue_label = 'Threshold'
limits = pd.DataFrame([
    {hue_label: 'high', 'value':  all_limits.loc[ismatch(Coverage='Main', Region='World'), 'Total'][0], 'note': 'Global Preventative Limit',},
    {hue_label: 'med', 'value':  all_limits.loc[ismatch(Coverage='Main', Region='World'), 'Onshore'][0], 'note': 'Global Onshore Limit',},
    {hue_label: 'low', 'value':  all_limits.loc[ismatch(Coverage='Oil and Gas', Region='World'), 'Total'][0], 'note': 'Global Limit with Current Facilities',},
]).set_index(hue_label)

# %%
all_limits

# %%
limits

# %%
limits.loc['high', 'value']

# %% [markdown]
# # Global Exceedance

# %%
data = (
    pd.concat((cdf['End of Century'], zdf[['Net Zero GHGs', 'Net Zero CO2']]), axis=1)
    .join(mdf, on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
data.head()

# %%

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
colors = {
    'low': 'plum',
    'med': 'orange',
    'high': 'orangered',
}

def add_spans(ax, limits, orient='h'):
    func = ax.axvspan if orient == 'h' else ax.axhspan
    get = lambda l: limits.loc[l, 'value'] * 1e3
    func(0, get('low'), color='plum', alpha=0.25, zorder=0)
    func(get('low'), get('med'), color='orange', alpha=0.25, zorder=0)
    func(get('med'), get('high'), color='orangered', alpha=0.25, zorder=0)
    xmax = ax.get_xlim()[1] if orient == 'h' else ax.get_ylim()[1]
    if xmax > get('high'):
        func(get('high'), xmax, color='black', alpha=0.25, zorder=0)


# %%
mdata = data.melt(id_vars=['Category', cat_label], value_vars=['Net Zero CO2', 'End of Century'], ignore_index=False)
mdata = mdata.where(mdata.Category.isin(label_mapping.keys()))
mdata.head()

# %%

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(7, 12))

palette = {
    'Net Zero CO2': 'thistle', 
    'End of Century': 'mediumpurple',
}

_data = mdata.loc[ismatch(Region='World', Variable='Cumulative Carbon Sequestration|CCS')].reset_index(drop=True)
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

add_spans(ax, limits, orient='v')
#ax.axhline(limits.loc['high', 'value'] * 1e3 * 0.5, c='k', ls='--', label='1/2 of Preventative Boundary')
ax.legend(loc='upper right')
ax.set_ylabel('Cumulative Stored CO2 (Mt)')
ax.set_xlabel('')
#plt.xticks(rotation=90)

fig.savefig('./figure_3b.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig('./figure_3b.png', bbox_inches='tight', dpi=1e3)

# %% [markdown]
# # Years of storage at net-zero levels
#
# We look at the difference between cumulative CO2 stored at net-zero compared to the boundary, and then divide by the rate at net-zero.

# %%
limits


# %%
def calc_time_to_limit(value, note):
    limit = value * 1e3
    nz_value = zdf.loc[ismatch(Variable='Cumulative Carbon Sequestration|CCS', Region='World'), 'Net Zero CO2'].reset_index(level=['Variable'], drop=True)
    nz_rate= zdf.loc[ismatch(Variable='Carbon Sequestration|CCS', Region='World'), 'Net Zero CO2'].reset_index(level=['Variable'], drop=True)
    return ((limit - nz_value) / nz_rate).pix.assign(**{hue_label: note})

time_to_limit = pd.concat([calc_time_to_limit(row['value'], row['note']) for i, row in limits.iterrows()])
time_to_limit

# %%
tdata = (
    time_to_limit.to_frame(name='Years to Exceed at Net-zero CO2 Levels')
    .join(mdf, on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
add_label_mapping(tdata, drop=True)
tdata.head()

# %%
FIGSIZE = (10, 3)

# %%
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=FIGSIZE)

sns.boxplot(
        data=tdata.reset_index(hue_label, drop=False).reset_index(drop=True),
        x='Years to Exceed at Net-zero CO2 Levels',
        y=cat_label,
        hue=hue_label,
        order=label_mapping.values(),
        showfliers=False,
#        inner='quart',
#        split=True,
#        cut=0,
        ax=ax,
        palette=[colors['high'], colors['med'], colors['low']],
        ).set(ylabel='')


fig.savefig('./figure_3c.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig('./figure_3c.png', bbox_inches='tight', dpi=1e3)

# %% [markdown]
# # Years until boundary is reached

# %%
ydf = cdf.loc[ismatch(Variable='Cumulative Carbon Sequestration|CCS', Region='World')].rename(columns={'End of Century': '2100'})
ydf.columns = ydf.columns.astype(int)
ydf[list(range(2101, 2301))] = np.nan
extrap_ydf = ydf.interpolate(method="slinear", fill_value="extrapolate", limit_direction="both", axis=1)
extrap_ydf.head()

# %%
limit = limits.loc['high', 'value'] * 1e3
year_exceedance = (extrap_ydf > limit).idxmax(axis=1)
year_exceedance[year_exceedance == 1990] = np.nan
year_exceedance.head()


# %%

def calc_year_exceedance(value, note):
    limit = value * 1e3
    year_exceedance = (extrap_ydf > limit).idxmax(axis=1)
    year_exceedance[year_exceedance == 1990] = np.nan
    return year_exceedance.pix.assign(**{hue_label: note})

year_exceedance = pd.concat([calc_year_exceedance(row['value'], row['note']) for i, row in limits.iterrows()])
year_exceedance

# %%
ydata = (
    year_exceedance.to_frame(name='Exceedance Year')
    .join(mdf, on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
add_label_mapping(ydata, drop=True)
ydata.head()

# %%

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=FIGSIZE)


sns.boxplot(
        data=ydata.reset_index(hue_label, drop=False).reset_index(drop=True),
        x='Exceedance Year',
        y=cat_label,
        hue=hue_label,
        order=label_mapping.values(),
        showfliers=False,
#        inner='quart',
#        split=True,
#        cut=0,
        ax=ax,
        palette=[colors['high'], colors['med'], colors['low']],
        legend=False,
        ).set(ylabel='')


fig.savefig('./figure_3d.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig('./figure_3d.png', bbox_inches='tight', dpi=1e3)

# %% [markdown]
# # Regional Exceedance
#
# **TODO** Move this to its own notebook

# %%
regions = limits.pix.unique('Region')[limits.pix.unique('Region').str.startswith('R5')]

for region in regions:
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(10, 15))

    sns.violinplot(
            data=mdata.loc[ismatch(Region=region, Variable='Cumulative Carbon Sequestration|CCS')].reset_index(drop=True),
            y='value',
            hue='variable',
            x='Category',
            order=cats,
            inner='quart',
            split=True,
            cut=0,
            ax=ax,
            )

    limit = limits.loc[region, 'Net total storage'] * 1e3
    ax.set_title(region)
    ax.axhspan(limit, ax.get_ylim()[1], color='red', alpha=0.25, zorder=0)

# %%

# %%
limits

# %%

# %%
limits

# %%
tdata = (
    time_to_limit.to_frame(name='Years to Exceed at Net-zero CO2 Levels')
    .join(mdf, on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
tdata.head()

# %%

# %%

# %%
# TODO: ???? compare with other plot; answer - different limit applied

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(15, 5))

sns.boxplot(
        data=tdata.reset_index(drop=True),
        x='Years to Exceed at Net-zero CO2 Levels',
        y='Category',
        order=cats,
#        inner='quart',
#        split=True,
#        cut=0,
        ax=ax,
        color='slategrey'
        )

ax.set_xlim(0, 400)

fig.savefig('./figure_3c.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig('./figure_3c.png', bbox_inches='tight', dpi=1e3)

# %%

# %%
# TODO: ???? compare with other plot; answer - different limit applied

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(15, 5))

sns.boxplot(
        data=tdata.reset_index(drop=True),
        x='Years to Exceed at Net-zero CO2 Levels',
        y='Category',
        order=cats,
#        inner='quart',
#        split=True,
#        cut=0,
        ax=ax,
        color='slategrey'
        )

ax.set_xlim(0, 400)

fig.savefig('./figure_3c.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig('./figure_3c.png', bbox_inches='tight', dpi=1e3)

# %% [markdown]
# # Years until boundary is reached

# %%
ydf = cdf.loc[ismatch(Variable='Cumulative Carbon Sequestration|CCS', Region='World')].rename(columns={'End of Century': '2100'})
ydf.columns = ydf.columns.astype(int)
ydf[list(range(2101, 2301))] = np.nan
extrap_ydf = ydf.interpolate(method="slinear", fill_value="extrapolate", limit_direction="both", axis=1)
extrap_ydf.head()

# %%
limit = limits.loc['World', 'Net total storage'] * 1e3
year_exceedance = (extrap_ydf > limit).idxmax(axis=1)
year_exceedance[year_exceedance == 1990] = np.nan
year_exceedance.head()


# %%
ydata = (
    year_exceedance.to_frame(name='Exceedance Year')
    .join(mdf, on=['Model', 'Scenario'])
    .replace(to_replace={'Category': ['failed-vetting', 'no-climate-assessment']}, value=np.nan)
    .dropna(subset='Category')
)
ydata.head()

# %%
# TODO: add fraction of scenarios in category in this dataset

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(15, 5))

sns.violinplot(
        data=ydata.reset_index(drop=True),
        x='Exceedance Year',
        y='Category',
        order=cats,
        inner='quart',
        split=True,
        cut=0,
        ax=ax,
        color='slategrey'
        )

fig.savefig('./figure_3d_violin.pdf', bbox_inches='tight', dpi=1e3)

# %%
# TODO: ???? compare with other plot

sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(15, 5))

sns.boxplot(
        data=ydata.reset_index(drop=True),
        x='Exceedance Year',
        y='Category',
        order=cats,
#        inner='quart',
#        split=True,
#        cut=0,
        ax=ax,
        color='slategrey'
        )


fig.savefig('./figure_3d.pdf', bbox_inches='tight', dpi=1e3)
fig.savefig('./figure_3d.png', bbox_inches='tight', dpi=1e3)

# %% [markdown]
# # Regional Exceedance

# %%
regions = limits.pix.unique('Region')[limits.pix.unique('Region').str.startswith('R5')]

for region in regions:
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(10, 15))

    sns.violinplot(
            data=mdata.loc[ismatch(Region=region, Variable='Cumulative Carbon Sequestration|CCS')].reset_index(drop=True),
            y='value',
            hue='variable',
            x='Category',
            order=cats,
            inner='quart',
            split=True,
            cut=0,
            ax=ax,
            )

    limit = limits.loc[region, 'Net total storage'] * 1e3
    ax.set_title(region)
    ax.axhspan(limit, ax.get_ylim()[1], color='red', alpha=0.25, zorder=0)

# %%
