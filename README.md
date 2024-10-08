# Overview

This is the analysis repository for Gidden et al. (2024).

# Notebooks

All notebooks here are in the form of python files, which can be synced as
jupyter notebooks with the
[jupytext](https://jupytext.readthedocs.io/en/latest/paired-notebooks.html)
tool, e.g.,

```bash
    $ jupytext --sync notebook.py # generates a notebook.ipynb file
```

If you make a material change to `notebook.ipynb`, you can resync it manually if
needed with


```bash
    $ jupytext --sync notebook.ipynb # updates the notebook.py file
```

# Assessment

The `assessment` folder holds all workflow code as Jupyter notebooks. To fully
   replicate this workflow, they should be run in numerical order. The numerical
   order has meaning as follows:
   1. `100` series notebooks read data from original data sources,
      process it, and place it in the `data/derived` folder
   2. `200` series notebooks use processed data to perform analysis and create
      figure-ready datasets together with figures
   3. `300` series notebooks generate tables, SI figures, and fact bases for
      statements made in the paper 

## Data

Raw data needed to reproduce this analysis needs to be placed in `2024_gidden_cstorage/data/raw` includes:

1. [AR6 Scenario Data](https://data.ene.iiasa.ac.at/ar6/#/workspaces)
    - `AR6_Scenarios_Database_World_v1.1.csv`
    - `AR6_Scenarios_Database_R5_regions_v1.1.csv`
    - `AR6_Scenarios_Database_R10_regions_v1.1.csv`
    - `AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx`
2. [PRIMAP Emissions Data](https://www.pik-potsdam.de/paris-reality-check/primap-hist/)
    - `Guetschow-et-al-2021-PRIMAP-hist_v2.3.1_20-Sep_2021.csv`
3. [Carbon Major Emission Data](https://carbonmajors.org/Downloads)
    - `emissions_low_granularity.csv`
4. [World Bank Socioeconomic data](https://data.worldbank.org/indicator)
    - `API_NY.GDP.PCAP.PP.KD_DS2_en_csv_v2_45514.csv`
    - `API_SP.POP.TOTL_DS2_en_csv_v2_34.csv`

Data in `2024_gidden_cstorage/data/packaged` comes directly with this repository
and is subject to its license. Any further use of this data must be credited
back to the citation below.

Data in `2024_gidden_cstorage/data/derived` are generated from `100`-series
notebooks in this repository.

# Citation

Please cite as:

```
Gidden et al. A precautionary planetary boundary for geologic carbon storage. *Journal* (2024) 
```