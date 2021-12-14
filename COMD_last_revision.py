# Python 3.8.2 (tags/v3.8.2:7b3ab59, Feb 25 2020, 22:45:29) [MSC v.1916 32 bit (Intel)]
import time
import csv
import pandas as pd
import numpy as np
import smtplib
from email.message import EmailMessage
from comdirect_api.comdirect_client import ComdirectClient
from datetime import date
from params import COMD_client_id, COMD_client_secret, COMD_user, COMD_uuid, COMD_password, EMAIL_ADDRESS, EMAIL_PASSWORD


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
    time.sleep(15)  # sleep 30 to get photoTAN active
    client.activate_session()
    client.refresh_token()
    account_uuid = COMD_uuid
    transactions = client.get_account_transactions(
        account_uuid,
        paging_count=500,  # 45 is ~1 months worth of transactions.
    )
    # print(transactions['values'])
    return transactions['values']


def parse_data():

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


def monthly_data(months):

    na_vals = ['NA', 'None']
    df1 = pd.read_csv('data/COMD_review1raw.csv',
                      names=['Date', 'Amount', 'Description', 'Info'],
                      skiprows=2,  # need to skip at least 1 for header
                      na_values=na_vals)
    # df1['Description'] = df1.Description.str.split(':', expand=True)[1]
    # df1['Description'] = df1.Description.str.split('}', expand=True)[0]
    # merge
    df2 = pd.read_excel('raw_data/2021_Übersicht_PayPal_20211209.xlsx')
    df = df1.append(df2, ignore_index=True)

    df.Description = np.where(df.Description.isnull(), df.Info, df.Description)
    df['Description'].fillna(df['Info'])  # very similar command to the above?
    df['Description'] = np.where(df['Description'].str.startswith('01'), df['Description'].str[2:], df['Description'])
    df['Supermarkt'] = np.where(df['Description'].str.contains(
        'BIO COMPANY|EDEKA|PaySqu|PAYONE|NETTO|ALDI|Schäf|NAH UND|ZEIT FUER|ALNATUR|DER KUCH|CAFE LEBENS|BAECKER|Bio Kondit|unverpackt|REWE|WURST|Lebensmittell|LIDL|SCHAEFERS|MASYMAS|MERCADONA|TGB LOS TOMAS|Kamps',
        case=False), df['Amount'], np.nan)
    df['Miete/Wohnen'] = np.where(df['Description'].str.contains(
        'Telefonica|IKEA|Stadtwerke|OVAG|Miet|Helpling|Wohn|Glühbirne|Rundfunk|BAUHAUS|Betriebskos|MONATSABRE|PORTA|Amazon|Kd-Nr.: 60522207|Vertragskonto 20|Infos zur Beitra',
        case=False), df['Amount'], np.nan)
    df['Drogerie'] = np.where(df['Description'].str.contains(
        'ROSSMANN|OEVERHAUS|Apo Doc|DROGERIE|APOTHEKE|2106104511505582|Mueller sagt Dan|0911164311887772|ApoNeo',
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

    df_months = dict()
    df_months[months] = df[(df['Month'] == months)]
    for key, value in df_months.items():
        if key in months:
            df_months[key].to_csv(f'data/{months}data.csv')  # month individual file
            df_months[key].to_csv(f'raw_data/COMD-processed.csv', mode='a', header=False)  # append main csv file

    # summary of months
    df_totals = dict()
    month_grp = df.groupby(['Month'])
    df_totals[months] = {
        'Month': months,
        'Supermarkt': month_grp['Supermarkt'].sum().loc[months],
        'Oliver': month_grp['Oliver'].sum().loc[months],
        'Drogerie': month_grp['Drogerie'].sum().loc[months],
        'Miete/Wohnen': month_grp['Miete/Wohnen'].sum().loc[months],
        'Essen_gehen': month_grp['Essen_gehen'].sum().loc[months],
        'Reise/Freizeit': month_grp['Reise/Freizeit'].sum().loc[months],
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


def email_files():

    msg = EmailMessage()
    msg['Subject'] = 'Comdirect files Jan - Jun 2021'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content('Final version, files attached.')
    files = [
        'data/Month_totals_21_data1.csv',
        'data/Archive/COMD-processed.csv',
        'data/Novemberdata.csv'
    ]

    for file in files:
        with open(file, 'rb') as f:
            file_data = f.read()
            file_type = f.name
            file_name = f.name
        msg.add_attachment(file_data, maintype='text', subtype=file_type, filename=file_name)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def main():

    parse_data()  # api call for new data
    
    monthly_data('November')  # log data into csv
    # email_files()


if __name__ == "__main__":
    main()

# TODO if you want visualize your results in a dashboard (Qlik or Tableau
