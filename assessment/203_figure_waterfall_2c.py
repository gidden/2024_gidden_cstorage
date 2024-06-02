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
import seaborn as sns
import numpy as np
from pathlib import Path

import plotnine as p9


# %%
data_path = Path('../data/packaged')
figure_path = Path('../figures')

# %%
df = pd.read_excel(data_path / 'table_fig2b.xlsx', sheet_name='table_fig2b')
df

# %%
df['id'] = range(len(df), 0, -1)
df['Total'] = df['Onshore'] + df['Offshore']
df['ymax'] = 2 * list([df.iloc[0]['Total'],]) + list(df.iloc[0]['Total'] - df.iloc[1:-2]['Total'].cumsum() ) + list([df.iloc[-1]['Total']])
df['ymin'] = [0] + list(df.iloc[1:-1]['ymax'] - df.iloc[1:-1]['Total']) + [0]
df

# %%
xwidth = 0.2
# specific wranging to get categories in the right order
data = (
    df.melt(
        id_vars=['Category', 'id', 'ymin', 'ymax'], 
        value_vars=['Onshore', 'Offshore'],
        var_name='Location',
        )
    .sort_values(['id', 'Location'])
    .assign(
        xmin=lambda _df: _df.id - xwidth,
        xmax=lambda _df: _df.id + xwidth,
        cat=lambda _df: pd.Categorical(_df.Category, categories=pd.unique(_df.Category))#[::-1])
    )
)
# separately calculation onshore/offshore ymin/ymax
data['ymax'][::2] = data['ymin'][::2] + data['value'][::2]
data['ymin'][1::2] = data['ymax'][::2]
data = data.assign(color=int(len(data) / 2) * ['#E69800', '#7A8EF5'])
data

# %%
colors = {'Offshore': '#7A8EF5', 'Onshore': '#E69800'}

fig = (
    p9.ggplot(data, p9.aes('cat', 'value', fill='Location'))
    + p9.geom_rect(data, p9.aes(x='cat', xmin='xmin', xmax='xmax', ymin='ymin', ymax='ymax'))
    + p9.scale_fill_manual(values=colors)
    + p9.coord_flip()
    + p9.ylab('Carbon Storage Potential (Gt CO2)')
    + p9.xlab('')
    + p9.theme(figure_size=(8, 5))
)
fig.save(figure_path / 'figure_2b.pdf', bbox_inches='tight', dpi=1000)
fig

# %%
