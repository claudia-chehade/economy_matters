
import numpy as np
import pandas as pd
import datetime

import altair as alt
from vega_datasets import data

def convert_month(date : str):
    # 2020Jun
    year = date[0:4]
    month = date[4:]
    datetime_object = datetime.datetime.strptime(month, "%b")
    month_number = datetime_object.month
    return f'{year}-{month_number}' if month_number > 9 else f'{year}-0{month_number}'

def make_time_series(df_data):
    df_data.set_index(list(df_data.columns[[0]]), inplace=True)
    # change indices to sortable values
    df_data = df_data.rename(index = lambda x: convert_month(x))
    df_data.sort_index(axis=0, ascending=True, inplace=True)
    df_data.index.name = 'Year / Months'
    return df_data

def reduce_data(df_data, suffix, columns_to_be_dropped=None, countries_to_be_dropped=None):
    df_data_reduced = df_data.copy()
    # split into two dataframes with average and end of period
    if columns_to_be_dropped:
        df_data_reduced.drop(columns_to_be_dropped, axis=1, inplace=True)   
        
    # drop lines with units and category    
    df_data_reduced.drop(index=1, axis=0, inplace=True)
    df_data_reduced.drop(index=2, axis=0, inplace=True)
    
    # set countries as column header
    df_data_reduced.columns = df_data_reduced.iloc[0]
    
    # drop countries (now duplicated line) 
    df_data_reduced.drop(df_data_reduced.index[0], inplace=True)
    
    # make the month column to index, convert the format and sort it ascending
    df_data_reduced = make_time_series(df_data_reduced)
    
    # remove all other stuff from country columns header
    df_data_reduced.rename(columns=lambda x: x[:-len(suffix)] if (type(x) is not float and x.endswith(suffix)) else x, inplace=True)
    
    # drop countries with low target2 saldos
    if countries_to_be_dropped:
        df_data_reduced.drop(countries_to_be_dropped, axis=1, inplace=True)
    
    # replace missing values by 0
    df_data_reduced.replace(to_replace='-', value='0', inplace=True)
    df_data_reduced.fillna(0, inplace=True)
    
    # convert objects to floats
    df_data_reduced = df_data_reduced.astype(float)    
    
    return df_data_reduced

def plot_time_series_with_vertical_selector(df_data, x_value, y_value, var_name):
    source = df_data
    source = source.reset_index().melt(x_value, var_name=var_name, value_name=y_value)

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=[x_value], empty='none')

    # The basic line
    line = alt.Chart(source).mark_line(interpolate='basis').encode(
        x=f'{x_value}:T',
        y=f'{y_value}:Q',
        color=f'{var_name}:N'
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(source).mark_point().encode(
        x=f'{x_value}:T',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 
                        f'{y_value}:Q',
                        alt.value(' '))
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart(source).mark_rule(color='gray').encode(
        x=f'{x_value}:T',
    ).transform_filter(
        nearest
    )

    # Put the five layers into a chart and bind the data
    return alt.layer(
        line, selectors, points, rules, text
    ).properties(
        width=600, height=500
    )

  