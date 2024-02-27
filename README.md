# Overview

This is an analysis repository. It has the following structure:

1. The `assessment` folder holds all workflow code as Jupyter notebooks. To
   fully replicate this workflow, they should be run in numerical order. The
   numerical order has meaning as follows:
   1. `100` series notebooks read data from original IAM database sources,
      process it, and place it in the `processed_data` folder
   2. `200` series notebooks read data from non-IAM sources, process it, and
      place it in the `processed_data` folder
   3. `300` series notebooks use processed data to perform analysis and create
      figure-ready datasets together with figures
2. The `scripts` folder holds additional processing code which is not
   meaningfully relevant to understand the analysis
3. The `definitions` folder holds files used to define thresholds or other
   quantities used in the analysis

## Environment File

This repo requires an environment file to be created with the name `.env`
sitting in the root directory (see `.env.sample`). It requires the following
paths to be defined: 
- `AR6_RAW`: path to the v1.1 R5 + World ALL_CLIMATE AR6 data
- `AR6_META`: path to the v1.1 AR6 meta data

# Thank yous

This analysis repo is based on a setup piloted by @gaurav-ganti - thank you
Gaurav!