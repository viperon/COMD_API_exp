import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def read_and_merge():
    data = pd.read_csv('data/COMD_review1raw.csv')
    df2 = pd.read_excel('raw_data/2021_Übersicht_PayPal_20211209.xlsx')
    df = data.append(df2, ignore_index=True)
    return df

def process_filters():
    df = read_and_merge()
    df.Description = np.where(df.Description.isnull(), df.Info, df.Description)
    df['Description'].fillna(df['Info'])  # very similar command to the above?
    df['Description'] = np.where(df['Description'].str.startswith('01'), df['Description'].str[2:], df['Description'])
    # FILTERS
    df['Supermarkt'] = np.where(df['Description'].str.contains(
        'BIO COMPANY|EDEKA|PaySqu|PAYONE|NETTO|ALDI|Schäf|NAH UND|ZEIT FUER|ALNATUR|DER KUCH|CAFE LEBENS|BAECKER|Bio Kondit|unverpackt|REWE|WURST|Lebensmittell|LIDL|SCHAEFERS|MASYMAS|MERCADONA|TGB LOS TOMAS|Kamps',
        case=False), df['Amount'], np.nan)
    df['Miete/Wohnen'] = np.where(df['Description'].str.contains(
        'Telefonica|IKEA|Stadtwerke|OVAG|Miet|Helpling|Wohn|Glühbirne|Rundfunk|BAUHAUS|Betriebskos|MONATSABRE|PORTA|Amazon|Kd-Nr.: 60522207|Vertragskonto 20|Infos zur Beitra',
        case=False), df['Amount'], np.nan)
    df['Drogerie'] = np.where(df['Description'].str.contains(
        'ROSSMANN|OEVERHAUS|Apo Doc|DROGERIE|APOTHEKE|2106104511505582|Mueller sagt Dan|0911164311887772',
        case=False), df['Amount'], np.nan)
    df['Essen_gehen'] = np.where(df['Description'].str.contains(
        'SUSHI|Funky Fisch|ISHIN|BURGER|Imbiss|RESTAURANT|ORIENT MASTER|PHO 56',
        case=False), df['Amount'], np.nan)
    df['Oliver'] = np.where(df['Info'].str.contains(
        'Oliver|Limango|Vinted|LANGERBLO|0121340000|M BERLIN|Baby|Vertbaudet|Kinder|sigikid|Depot-Spa|BALLONHE|GROW',
        case=False), df['Amount'], np.nan)
    df['Reise/Freizeit'] = np.where(df['Description'].str.contains(
        'Blocsport|Boulder|LATE SHOP|Carsharing|DECATHLON|BERLINER VERKEHR|JAVE|Paint Your Style', case=False), df['Amount'], np.nan)

    df.fillna(0, inplace=True)
    df.Info = np.where(df.Info.str.startswith('None'), df.Description, df.Info)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df['Month'] = df['Date'].dt.month_name()
    return df


def split_dfs():
    df = process_filters()
    df.sort_values(by='Date', inplace = True)
    df_income = df[df['Amount'] > 0]
    df_income = df_income[['Date', 'Amount', 'Info', 'Description', 'Month']]
    df_payments = df[df['Amount'] < 0]
    return df_income, df_payments


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

def viz_month(overview): 
    plt.figure(figsize=(15,5))
    plt.bar(overview.index, abs(overview[f'{overview.columns[0]}']))
    plt.title(f'{overview.columns[0]}')
    plt.grid()
    plt.show()
    
def main(month_choice, graphs=False):
    overview = set_month_overview(month_choice)
    if graphs == True:
        viz_month(overview)
    return overview

def yearly_view(miete=True):
    df_main = main('June').join(main('July').join(main('August')).join(main('September')).join(main('October')).join(main('November')))
    if miete == False:
        return df_main.drop('Miete/Wohnen', axis=0)
    return df_main



def set_income():
    df_income, df_payments = split_dfs()
    df_income = df_income.groupby('Month').sum('Amount') # includes paypal
    df_income = df_income.reset_index().drop([2, 5, 6], axis=0)

    df_income.set_index('Month', inplace=True)
    df_income = df_income.reindex(['June', 'July', 'August', 'September', 'October', 'November'])
    df_income.columns = ['Income']
    return df_income

def set_expenditure():
    current_months = ['June', 'July', 'August', 'September', 'October', 'November']
    totals = {}
    for i in current_months:
        df_sum = main(i).sum()
        totals[f'{i}'] = [float(df_sum)]
    df_expenditure = pd.DataFrame(totals).T
    df_expenditure.columns = ['Expenditure']
    return df_expenditure



if __name__ == "__main__":
    yearly_view()
    main('June', graph=True)
    detail_monthly_payments('June')
