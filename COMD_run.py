import time
import csv
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
from comdirect_api.comdirect_client import ComdirectClient
from datetime import date
from params import COMD_client_id, COMD_client_secret, COMD_user, COMD_uuid, COMD_password, EMAIL_ADDRESS, EMAIL_PASSWORD

# API CALL
def client_connection():
    """
    Connect to Com-direct API, request transaction details and parse it into dictionary.
    """
    client_id = COMD_client_id
    client_secret = COMD_client_secret
    client = ComdirectClient(client_id, client_secret)
    # credentials
    user = COMD_user
    password = COMD_password
    client.fetch_tan(user, password)
    time.sleep(15)  # sleep to get photoTAN active
    client.activate_session()
    client.refresh_token()
    account_uuid = COMD_uuid
    transactions = client.get_account_transactions(
        account_uuid,
        paging_count=350,  # 45 is ~1 months worth of transactions.
    )
    # print(transactions['values'])
    return transactions['values']


def parse_data(): # calls client API
    """
    call client_connection()
    parses api dictionary response into CSV for records and future data appending.
    """
    today = date.today()
    transactions_dict = dict()
    for item in client_connection():
        transactions_dict['Date'] = item['bookingDate']
        if transactions_dict['Date'] is None:
            transactions_dict['Date'] = today
        transactions_dict['Amount'] = item['amount']['value']
        try:
            transactions_dict['Description'] = item['remitter'].get('holderName', None)
        except AttributeError:
            transactions_dict['Description'] = 'None'
        transactions_dict['Info'] = item['remittanceInfo'][:18]
        try:
            with open('data/COMD_review1raw.csv', 'a', encoding='utf-8') as document:
                writer = csv.writer(document)
                writer.writerow(
                    [transactions_dict['Date'],
                     transactions_dict['Amount'],
                     transactions_dict['Description'],
                     transactions_dict['Info'],
                     ])
        except TypeError as e:
            print(e, '\n line missed')
            

# READING FILES and pre-processing
def clean_data():
    """
    reads api call dictionary and merges paypal CSVs, clean data for filtering
    """
    df1 = pd.read_csv('data/COMD_review1raw.csv')
    df2 = pd.read_excel('raw_data/2021_Übersicht_PayPal_20211209.xlsx')
    df = df1.append(df2, ignore_index=True)
    df.Description = np.where(df.Description.isnull(), df.Info, df.Description)
    df['Description'].fillna(df['Info'])
    df['Description'] = np.where(df['Description'].str.startswith('01'), df['Description'].str[2:], df['Description'])
    df.Info = np.where(df.Info.str.startswith('None'), df.Description, df.Info)
    
    df['information'] = df['Info'] +' '+ df['Description']
    df = df.drop(['Info', 'Description'], axis=1)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df['Month'] = df['Date'].dt.month_name()
    df.sort_values(by='Date', inplace = True)
    
    return df

def process_filters():
    """
    splits data into categories
    """
    df = clean_data()
    df['Supermarkt'] = np.where(df['information'].str.contains(
        'BIO COMPANY|EDEKA|PaySqu|PAYONE|NETTO|ALDI|Schäf|NAH UND|ZEIT FUER|ALNATUR|DER KUCH|CAFE LEBENS|BAECKER|Bio Kondit|unverpackt|REWE|WURST|Lebensmittell|LIDL|SCHAEFERS|MASYMAS|MERCADONA|TGB LOS TOMAS|Kamps|JAVE',
        case=False), df['Amount'], np.nan)
    df['Miete/Wohnen'] = np.where(df['information'].str.contains(
        'Telefonica|IKEA|Stadtwerke|OVAG|Miet|Helpling|Wohn|Glühbirne|Rundfunk|BAUHAUS|Betriebskos|MONATSABRE|PORTA|Amazon|Kd-Nr.: 60522207|Vertragskonto 20|Infos zur Beitra|Rueckzahlung|Versicherung|BUERGERDIENSTE',
        case=False), df['Amount'], np.nan)
    df['Drogerie'] = np.where(df['information'].str.contains(
        'ROSSMANN|OEVERHAUS|Apo Doc|DROGERIE|APOTHEKE|2106104511505582|Mueller sagt Dan|0911164311887772|ApoNeo',
        case=False), df['Amount'], np.nan)
    df['Essen_gehen'] = np.where(df['information'].str.contains(
        'SUSHI|Funky Fisch|ISHIN|BURGER|Imbiss|RESTAURANT|ORIENT MASTER|PHO 56',
        case=False), df['Amount'], np.nan)
    df['Oliver'] = np.where(df['information'].str.contains(
        'Oliver|Limango|Vinted|LANGERBLO|0121340000|M BERLIN|Baby|Vertbaudet|Kinder|sigikid|Depot-Spa|BALLONHE|GROW',
        case=False), df['Amount'], np.nan)
    df['Reise/Freizeit'] = np.where(df['information'].str.contains(
        'Blocsport|Boulder|LATE SHOP|Carsharing|DECATHLON|BERLINER VERKEHR|Paint Your Style|ULLRICH', case=False), df['Amount'], np.nan)
    df.fillna(0, inplace=True)
    df_columns = ['Date', 'Amount', 'information', 'Supermarkt', 'Miete/Wohnen',
       'Drogerie', 'Essen_gehen', 'Oliver', 'Reise/Freizeit', 'Month']
    df = df[df_columns]
    return df


def log_month_to_csv(months, append_year_csv=False, month_totals=False):
    """
    pulls filtered data and slices a view of the month of choice.
    option of logging into year CSV and month totals CSV
    """
    df = process_filters()
    
    df_months = dict()
    df_months[months] = df[(df['Month'] == months)]
    for key, value in df_months.items():
        if key in months:
            df_months[key].to_csv(f'data/{months}data.csv')  # month individual file
            df_months[key].to_csv(f'raw_data/COMD-processed.csv', mode='a', header=False)  # append main csv file
    
    if month_totals:
        # summary of months
        df_totals = dict()
        month_grp = df.groupby(['Month'])
        df_totals[months] = {
            'Month': months,
            'Supermarkt': round(month_grp['Supermarkt'].sum().loc[months], 2),
            'Oliver': round(month_grp['Oliver'].sum().loc[months], 2),
            'Drogerie': round(month_grp['Drogerie'].sum().loc[months], 2),
            'Miete/Wohnen': round(month_grp['Miete/Wohnen'].sum().loc[months], 2),
            'Essen_gehen': round(month_grp['Essen_gehen'].sum().loc[months], 2),
            'Reise/Freizeit': round(month_grp['Reise/Freizeit'].sum().loc[months], 2),
            'Totals': round(month_grp['Amount'].sum().loc[months], 2),
        }

        csv_file = "data/Month_totals_21_data1.csv"
        csv_columns = ['Month',
                       'Supermarkt',
                       'Oliver',
                       'Drogerie',
                       'Miete/Wohnen',
                       'Essen_gehen',
                       'Reise/Freizeit',
                       'Totals',
                       ]
        try:
            with open(csv_file, 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writerow(df_totals[months])  # append monthly summary details to year file
        except IOError:
            print("I/O error")
        


if __name__ == "__main__":

    # API CALL data appends into COMD_review1raw.csv
    # parse_data()  # calls client connection
    
    # LOG TO CSV
    # log a specific month by writing into a csv, calls process_filters
    # last month ran
    log_month_to_csv('June', append_year_csv=False, month_totals=True)
    log_month_to_csv('July', append_year_csv=False, month_totals=True)
    log_month_to_csv('August', append_year_csv=False, month_totals=True)
    log_month_to_csv('September', append_year_csv=False, month_totals=True)
    log_month_to_csv('October', append_year_csv=False, month_totals=True)
    log_month_to_csv('November', append_year_csv=False, month_totals=True)
