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


# %%
data_path = Path('../data/packaged')
raw_path = Path('../data/raw')
figure_path = Path('../figures')

# %%
Data=pd.read_csv(data_path / 'responsibility_capacity_storage.csv')
Mapi=pd.read_csv(data_path / "R5_ISO_MAP.csv")
OP=pd.merge(Data,Mapi,left_on="ISO", right_on="iso3c",how="outer")

# %%
Emm=pd.read_csv(raw_path / "Guetschow-et-al-2021-PRIMAP-hist_v2.3.1_20-Sep_2021.csv")
Emm=Emm[(Emm["source"]=="PRIMAP-hist_v2.3.1")&
        (Emm["scenario (PRIMAP-hist)"]=="HISTTP")&
        (Emm["entity"]=="KYOTOGHG (AR4GWP100)")&
        (Emm["entity"]=="KYOTOGHG (AR4GWP100)")]

df=Emm.drop(['source', 'scenario (PRIMAP-hist)', 'entity', 'unit','category (IPCC2006_PRIMAP)'], axis=1)

A2=df.groupby("area (ISO3)").sum()
A2["Emission (billion tonne)"]=A2.sum(axis=1)
A2=A2.reset_index()
A2=A2[["area (ISO3)", "Emission (billion tonne)"]]


GDP=pd.read_csv(raw_path / "API_NY.GDP.PCAP.PP.KD_DS2_en_csv_v2_45514.csv", skiprows=4)
GDP=GDP[["Country Code","2019"]]
GDP["GDP/capita 2019"]=GDP["2019"]/1000

POP=pd.read_csv(raw_path / "API_SP.POP.TOTL_DS2_en_csv_v2_34.csv",skiprows=4)
POP=POP[["Country Code","2019"]]
POP["PPLN"]=POP["2019"]

OPX=pd.merge(OP,GDP,left_on="ISO",right_on="Country Code",how="inner")
OPX0=pd.merge(OPX,POP,left_on="ISO",right_on="Country Code",how="inner")
OPX1=pd.merge(OPX0,A2,left_on="ISO",right_on="area (ISO3)",how="inner")


OPX1["Percentage_Loss"]=(OPX1["Percentage_Loss"])*100
OPX1["EMM/cap"]=OPX1["Emission (billion tonne)"]/OPX1["PPLN"]
OPX1["L5"]=OPX1["Pot_OFF_Final"]+OPX1["Pot_ON_Final"]
OPXN=OPX1[OPX1["L5"]>0.001]
OPX2=OPXN.rename({'L5':'Net Storage Potential (GTCO2)',
                  "GDP/capita 2019":"GDP|PPP 2017($)('000) per Capita in 2019 ", 
                  "EMM/cap": "Cumulative emission (Gg CO2 eq) per Capita in 2019",
                  "r5_iamc":"R5 regional Classification"}, axis=1)


# %%
c1 = OPX2['Cumulative emission (Gg CO2 eq) per Capita in 2019'] > 1.5
c2 = OPX2['Cumulative emission (Gg CO2 eq) per Capita in 2019'] < 0.5
c3 = OPX2["Net Storage Potential (GTCO2)"] > 25
c4 = OPX2["Net Storage Potential (GTCO2)"] < .1
other = OPX2['iso3c'].isin(['IND', 'CHN', 'SAU', 'IRN', 'KWT'])

OPX2['keep_labels'] = OPX2.loc[((c1 | c2) & (c3 | c4)) | other, 'iso3c']

gdp_var = "GDP per capita\n(1000$)"
em_var = 'Cumulative Emissions in 2019 (Mt CO2 per capita)'
stor_var = "Preventative Storage Potential (Gt CO2)"
reg_var = 'IPCC Region'
rename = {
    "GDP|PPP 2017($)('000) per Capita in 2019 ": gdp_var,
    'Cumulative emission (Gg CO2 eq) per Capita in 2019': em_var, 
    "Net Storage Potential (GTCO2)": stor_var,
    'R5 regional Classification': reg_var,
}

plot = (
    p9.ggplot(OPX2.rename(columns=rename).dropna(subset=reg_var), p9.aes(em_var, stor_var, size=gdp_var))
    + p9.geom_point(p9.aes(color=reg_var))
    + p9.scale_y_log10() 
    + p9.scale_x_log10()
    + p9.theme(figure_size=(9, 6))
    + p9.geom_vline(xintercept=1, alpha=0.75, linetype='dotted')  
    + p9.geom_hline(yintercept=1, alpha=0.75, linetype='dotted')  
    + p9.geom_label(p9.aes(label="keep_labels"), 
                 size=8, alpha=0.5, 
                 nudge_y=0.055, nudge_x=-0.055, 
                 )
)
plot.save(figure_path / 'figure_4.pdf', bbox_inches='tight', dpi=1000)
plot
