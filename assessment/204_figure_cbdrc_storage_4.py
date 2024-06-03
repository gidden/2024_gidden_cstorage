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
#     display_name: ME_X86_P3.8
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
import seaborn as sns
import numpy as np
from pathlib import Path

import plotnine as p9

from pandas_indexing import ismatch


# %%
data_path = Path('../data/packaged')
raw_path = Path('../data/raw')
figure_path = Path('../figures')

# %% [markdown]
# # Storage

# %%
df = pd.read_csv(data_path / 'Analysis_dataset_20240602.csv')
mdf = pd.read_csv(data_path / "iso3c_region_mapping_20240602.csv")
sdf = pd.merge(df, mdf[['iso3c', 'r5_iamc']], left_on='ISO', right_on='iso3c', how='left').drop('ISO', axis=1).dropna(subset='iso3c').set_index('iso3c')
sdf['Pot_Final'] = sdf['Pot_OFF_Final'] + sdf['Pot_ON_Final']
sdf.head()

# %% [markdown]
# # Emissions

# %%
# Country-level territorial CO2 in kt 
tdf = pd.read_csv(raw_path / "Guetschow-et-al-2021-PRIMAP-hist_v2.3.1_20-Sep_2021.csv", index_col=list(range(6)))
tdf = tdf.loc[ismatch(**{
    'source': 'PRIMAP-hist_v2.3.1',
    'scenario (PRIMAP-hist)': 'HISTTP', # including 3rd party reporting
    'entity': 'CO2',
    'category (IPCC2006_PRIMAP)': 'M.0.EL', # national total excl LULUCF
})][pd.Series(range(1990, 2020), dtype=str)].cumsum(axis=1).pix.project('area (ISO3)').rename_axis(index='iso3c', columns='year')
tdf.head()

# %%
# country-level carbon major CO2 in Mt
cdf = (
    pd.merge(
        pd.read_csv(raw_path / "emissions_low_granularity.csv"),
        pd.read_excel(data_path / "carbon_major_iso_mapping.xlsx"),
        left_on='parent_entity',
        right_on='name',
    )
    .groupby(['iso3c', 'year'])['total_emissions_MtCO2e']
    .sum()
    .unstack('year')
    .fillna(method='ffill')
    [range(1990, 2020)]
    .multiply(1e3) # Mt to kt
    .cumsum(axis=1)
)
cdf.head()

# %%
edf = pd.concat([
    tdf.rename(columns={'2019': 'Territorial Emissions (1990-2019)'})['Territorial Emissions (1990-2019)'],
    cdf.rename(columns={2019: 'Carbon Major Emissions (1990-2019)'})['Carbon Major Emissions (1990-2019)'],
    ], axis=1)
edf

# %% [markdown]
# # Socio Economics

# %%
gdppc = (
    (pd.read_csv(raw_path / "API_NY.GDP.PCAP.PP.KD_DS2_en_csv_v2_45514.csv", skiprows=4, index_col=1)["2019"] / 1e3)
    .to_frame()
    .rename_axis(index='iso3c')
    .rename(columns={'2019': '2019 GDP / capita'})
)

pop = (
    (pd.read_csv(raw_path / "API_SP.POP.TOTL_DS2_en_csv_v2_34.csv", skiprows=4, index_col=1)["2019"])
    .to_frame()
    .rename_axis(index='iso3c')
    .rename(columns={'2019': '2019 population'})
)
pop.head()

# %% [markdown]
# # Plots

# %%
pdata = pd.concat([edf, gdppc, pop, sdf[sdf['Pot_Final'] > 0.01]], axis=1).reset_index()

tcol = 'Territorial CO2 Emissions (1990-2019) per capita'
pdata[tcol] = pdata['Territorial Emissions (1990-2019)'] / pdata['2019 population']
ccol = 'Carbon Major Emissions (1990-2019) per capita'
pdata[ccol] = pdata['Carbon Major Emissions (1990-2019)'] / pdata['2019 population']

pdata.head()


# %%
def plot(data, col):
    c1 = data[col] > 1.5
    c2 = data[col] < 0.5
    c3 = data["Pot_Final"] > 25
    c4 = data["Pot_Final"] < .1
    other = data['iso3c'].isin(['IND', 'CHN', 'SAU', 'IRN', 'KWT'])

    data['keep_labels'] = pdata.loc[((c1 | c2) & (c3 | c4)) | other, 'iso3c']

    gdp_var = "GDP per capita\n(1000$)"
    stor_var = "Preventative Storage Potential (Gt CO2)"
    reg_var = 'IPCC Region'
    rename = {
        "2019 GDP / capita": gdp_var,
        "Pot_Final": stor_var,
        'r5_iamc': reg_var,
    }

    return (
        p9.ggplot(data.rename(columns=rename).dropna(subset=[reg_var]), p9.aes(col, stor_var, size=gdp_var))
        + p9.geom_point(p9.aes(color=reg_var))
        + p9.scale_y_log10() 
        + p9.scale_x_log10()
        + p9.theme(figure_size=(9, 6))
        + p9.geom_label(p9.aes(label="keep_labels"), 
                    size=8, alpha=0.5, 
                    nudge_y=0.055, nudge_x=-0.055, 
                    )
        + p9.geom_vline(xintercept=7e-2, alpha=0.75, linetype='dotted')  
        + p9.geom_hline(yintercept=1, alpha=0.75, linetype='dotted') 
    )


# %%
p = plot(pdata, tcol)
p.save(figure_path / 'figure_4a.pdf', bbox_inches='tight', dpi=1000)
p

# %%
p = plot(pdata, ccol)
p.save(figure_path / 'figure_4b.pdf', bbox_inches='tight', dpi=1000)
p
