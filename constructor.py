import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from COMD_run import process_filters

# DISPLAY FUNCTIONS for front end

def split_dfs():
    """
    splits data into income and expenditure
    """
    df = process_filters().fillna(0)
    df_income = df[df['Amount'] > 0]
    df_income = df_income[['Date', 'Amount', 'information', 'Month']]
    df_payments = df[df['Amount'] < 0]
    return df_income, df_payments


def monthly_transactions(month, transactions='payments'):
    """
    monthly overview of payments or income.
    """
    df_income, df_payments = split_dfs()
    if transactions == 'income':
        return df_income[df_income['Month'] == month]
    return df_payments[df_payments['Month'] == month]

def yearly_view():
    # df = process_filters()
    month_list = ['June', 'July', 'August', 'September',  'October' ,'November']

    df_temp = set_month_overview('June')
    for index, month in enumerate(month_list):
        try:
            new_month = set_month_overview(month_list[index+1])
            df_temp = df_temp.join(new_month)
        except IndexError:
            print('end of months')
    
    df_temp['average'] = round(df_temp.sum(axis=1)/len(df_temp.T), 2)
    return df_temp


def detail_monthly_payments(month):
    """
    Displays all payments of a given month
    """
    df_income, df_payments = split_dfs()
    return df_payments[df_payments['Month'] == month]


def set_month_overview(months):
    
    df = process_filters()
    df_totals = dict()
    month_grp = df.groupby(['Month'])
    df_totals[months] = {
        'Supermarkt': month_grp['Supermarkt'].sum().loc[months],
        'Oliver': month_grp['Oliver'].sum().loc[months],
        'Drogerie': month_grp['Drogerie'].sum().loc[months],
        'Miete/Wohnen': month_grp['Miete/Wohnen'].sum().loc[months],
        'Essen_gehen': month_grp['Essen_gehen'].sum().loc[months],
        'Reise/Freizeit': month_grp['Reise/Freizeit'].sum().loc[months], 
    }
    new_df = pd.DataFrame(df_totals)

    return new_df


def set_income():
    df_income, df_payments = split_dfs()
    df_income = df_income.groupby('Month').sum('Amount')
    df_income = df_income.reset_index().drop([2, 5, 6], axis=0)

    df_income.set_index('Month', inplace=True)
    df_income = df_income.reindex(['June', 'July', 'August', 'September', 'October', 'November'])
    df_income.columns = ['Income']
    return df_income

def set_expenditure():
    current_months = ['June', 'July', 'August', 'September', 'October', 'November']
    totals = {}
    for i in current_months:
        df_sum = set_month_overview(i).sum()
        totals[f'{i}'] = [float(df_sum)]
    df_expenditure = pd.DataFrame(totals).T
    df_expenditure.columns = ['Expenditure']
    return df_expenditure



if __name__ == "__main__":
    yearly_view()
    detail_monthly_payments('June')
