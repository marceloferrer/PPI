# Basic analysis on bonds, showing mean and moving average. Then exporting to excel.
from ppi_client.models.account_movements import AccountMovements
from ppi_client.ppi import PPI
from ppi_client.models.orders_filter import OrdersFilter
from ppi_client.models.order_budget import OrderBudget
from ppi_client.models.order_confirm import OrderConfirm
from ppi_client.models.disclaimer import Disclaimer
from ppi_client.models.search_instrument import SearchInstrument
from ppi_client.models.search_marketdata import SearchMarketData
from ppi_client.models.search_datemarketdata import SearchDateMarketData
from ppi_client.models.order import Order
from ppi_client.models.instrument import Instrument
from datetime import datetime, timedelta
import asyncio
import json
import traceback
from openpyxl import Workbook
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np

# Change sandbox variable to False to connect to production environment
ppi = PPI(sandbox=False)

def api_to_dataframe(api_response):
    df_marketdata = pd.DataFrame(api_response)
    df_marketdata["date"] = pd.to_datetime(df_marketdata["date"].str[0:10])
    df_marketdata = df_marketdata.set_index(['date'])

    return df_marketdata

def main():
    try:
        # Change login credential to connect to the API
        ppi.account.login('User', 'Password')
        nombre1 = input("Ingrese nombre del primer bono a comparar\n")
        nombre2 = input("Ingrese nombre del segundo bono a comparar\n")
        dias = input("Ingrese la cantidad de días requeridos\n")

        now = datetime.now()
        previous = datetime.today() - timedelta(days=int(dias))

        # Obtengo las cotizaciones historicas
        print(f"Realizando busqueda de {nombre1} desde el {previous.strftime('%Y-%m-%d')}")
        market_data1 = ppi.marketdata.search(SearchDateMarketData(nombre1, "Bonos", "A-48HS",
                                                                  previous.strftime('%Y-%m-%d'),
                                                                  now.strftime('%Y-%m-%d')))

        market_data2 = ppi.marketdata.search(SearchDateMarketData(nombre2, "Bonos", "A-48HS",
                                                                  previous.strftime('%Y-%m-%d'),
                                                                  now.strftime('%Y-%m-%d')))

        df_market_data = api_to_dataframe(market_data1)
        df_market_data2 = api_to_dataframe(market_data2)

        print("\nGenerando medias")
        df1 = df_market_data[["price"]].copy()
        df2 = df_market_data2[["price"]].copy()

        df = df1.subtract(df2, fill_value=0)

        promedio = df[["price"]].rolling(window=df.shape[0]).mean()
        media10 = df["price"].rolling(window=10).mean()
        media30 = df[["price"]].rolling(window=30).mean()
        media100 = df[["price"]].rolling(window=100).mean()

        strPrecio = "Precio (%.4f)" % df[["price"]].iloc[-1]
        strPromedio = "Promedio (%.4f)" % promedio.iloc[-1]
        strMedia10 = "Media 10 días (%.4f)" % media10.iloc[-1]
        strMedia30 = "Media 30 días (%.4f)" % media30.iloc[-1]
        strMedia100 = "Media 100 días (%.4f)" % media100.iloc[-1]

        print(strPrecio)
        print(strPromedio)
        print(strMedia10)
        print(strMedia30)
        print(strMedia100)

        df["Promedio"] = promedio
        df["Media10"] = media10
        df["Media30"] = media30
        df["Media100"] = media100

        # Genero el grafico y lo muestro
        df[["price", "Promedio", "Media10", "Media30", "Media100"]].plot()
        plt.legend([strPrecio, strPromedio, strMedia10, strMedia30, strMedia100])
        plt.show(block=True)

        # Ordeno y exporto a excel
        df = df.sort_values(by="date", ascending=False)
        df.to_excel(f"{nombre1}-{nombre2} ({dias}) {now.strftime('%Y-%m-%d %H_%M')}.xlsx")

    except Exception as message:
        print(datetime.now())
        print(message)

    input('\nPress Enter to exit')


if __name__ == '__main__':
    main()

