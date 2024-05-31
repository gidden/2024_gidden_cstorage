# Overview

This is the analysis repository for Gidden et al. (2024).

The `assessment` folder holds all workflow code as Jupyter notebooks. To fully
   replicate this workflow, they should be run in numerical order. The numerical
   order has meaning as follows:
   1. `100` series notebooks read data from original data sources,
      process it, and place it in the `data/derived` folder
   2. `200` series notebooks generate tables and fact bases for statements made
      in the paper 
   3. `300` series notebooks use processed data to perform analysis and create
      figure-ready datasets together with figures

## Data

Raw data needed to reproduce this analysis needs to be placed in `2024_gidden_cstorage/data/raw` includes:

1. AR6 Scenario Data
    - `AR6_Scenarios_Database_World_v1.1.csv`
    - `AR6_Scenarios_Database_R5_regions_v1.1.csv`
    - `AR6_Scenarios_Database_R10_regions_v1.1.csv`
    - `AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx`

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