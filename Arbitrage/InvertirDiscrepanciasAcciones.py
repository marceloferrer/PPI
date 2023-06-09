### Automatically execute buy/sell operation when detecting discrepancies in the stock market

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
from termcolor import colored
import colorama
import asyncio
import json
import traceback

colorama.init()

# Change sandbox variable to False to connect to production environment
ppi = PPI(sandbox=False)


# BOLT queda afuera x problemas de mercado
tickers = ["AGRO", "AUSO", "BYMA", "CADO", "CEPU", "CRES", "CTIO", "CVH", "EDN", "HARG", "MIRG", "SUPV", "TECO2", "TGSU2"]
puntas = {
    "PESOS-INMEDIATA": 0,
    "AGRO-INMEDIATA": 0,
    "AGRO-A-48HS": 0,
    "CADO-INMEDIATA": 0,
    "CADO-A-48HS": 0,
    "CRES-INMEDIATA": 0,
    "CRES-A-48HS": 0,
    "CEPU-INMEDIATA": 0,
    "CEPU-A-48HS": 0,
    "CTIO-INMEDIATA": 0,
    "CTIO-A-48HS": 0,
    "HARG-INMEDIATA": 0,
    "HARG-A-48HS": 0,
    "MIRG-INMEDIATA": 0,
    "MIRG-A-48HS": 0,
    "CVH-INMEDIATA": 0,
    "CVH-A-48HS": 0,
    "AUSO-INMEDIATA": 0,
    "AUSO-A-48HS": 0,
    "BYMA-INMEDIATA": 0,
    "BYMA-A-48HS": 0,
    "EDN-INMEDIATA": 0,
    "EDN-A-48HS": 0,
    "SUPV-INMEDIATA": 0,
    "SUPV-A-48HS": 0,
    "TECO2-INMEDIATA": 0,
    "TECO2-A-48HS": 0,
    "TGSU2-INMEDIATA": 0,
    "TGSU2-A-48HS": 0,
    "EJECUTANDOSE": 0
}

# Realiza la operacion de compra/venta
def operar(ticker, buy_price, sell_price):
    try:
        if puntas["EJECUTANDOSE"] == 0:
            puntas["EJECUTANDOSE"] = 1
        
            print(colored("\nRealizando compra %s - INM: %.2f" % (ticker, buy_price), "green"))
            buy = ppi.orders.confirm(OrderConfirm("NRO_COMITENTE", 20000, buy_price, ticker, "ACCIONES", "Dinero",
                                                  "PRECIO-LIMITE", "POR-EL-DIA", None, "Compra"
                                                  , "INMEDIATA", [], None))

            print(buy)
            print(colored("\Cantidad comprada %s - %.2f" % (ticker, buy['quantity']), "green"))

            #todo mejorar confirmacion de compra ejecutada para cargar la venta (se puede pedir por orden_id)
            for x in range(30):
                try:
                    print("\n Intento de venta numero %s" % x)
                    detail = ppi.orders.get_order_detail(Order(buy['id'], "NRO_COMITENTE", None))
                    print(detail)
                    
                    if detail['status'] == 'EJECUTADA':
                        print(colored("\nRealizando venta %s - 48Hs: %.2f" % (ticker, sell_price), "green"))
                        confirmation = ppi.orders.confirm(
                            OrderConfirm("NRO_COMITENTE", buy['quantity'], sell_price, ticker, "ACCIONES", "Papeles",
                                     "PRECIO-LIMITE", "HASTA-SU-EJECUCION", None, "Venta"
                                     , "A-48HS", [], None))
                        
                        print(confirmation)
                        quit()
                    else:
                        print("La orden aun no ha sido ejecutada")
                        if x == 35:
                            print("Cancelando la orden por exceso de tiempo")
                            cancel = ppi.orders.cancel_order(Order(buy['id'], "NRO_COMITENTE", None))
                            print(cancel)
                except Exception as error:
                    print(error)
            quit()
            
            #puntas["EJECUTANDOSE"] = 0
        else:
            print("\n Ya se esta ejecutando una operacion")
    except Exception as error:
        traceback.print_exc()
        quit()

# Evalua si realiza la compra (no tiene en cuenta segunda oferta de libro)
def evaluarPuntas(ticker):
    now = datetime.now()
    if now > now.replace(hour=15, minute=50, second=0, microsecond=0):
        print("Horario de inmediato por cerrar")
        quit()

    print(colored("Evaluando posible compra %s" % ticker, "green"))
    current_book_INM = ppi.marketdata.book(SearchMarketData(ticker, "Acciones", "INMEDIATA"))
    print(current_book_INM)
    if len(current_book_INM['offers']) > 0:
        buy_price = current_book_INM['offers'][0]['price']
        buy_tot = current_book_INM['offers'][0]['quantity'] * buy_price
    else:
        buy_price = 0
        buy_tot = 0

    current_book_48 = ppi.marketdata.book(SearchMarketData(ticker, "Acciones", "A-48HS"))
    print(current_book_48)
    if len(current_book_48['bids']) > 0:
        sell_price = current_book_48['bids'][0]['price']
        sell_tot = current_book_48['bids'][0]['quantity'] * sell_price
    else:
        sell_price = 0
        sell_tot = 0

    # Verifico que haya precios, que la liquidez sea de mas de $10000 y que no me quede comprado
    if buy_price > 0 and sell_price > 0:
        if sell_price > buy_price:
            if buy_tot >= 20000:
                if sell_tot >= 19000:
                    tasa_compra = (sell_price / buy_price) - 1
                    # La tasa se evalua por 4 para tener en cuenta comisiones
                    tasa_caucion = (puntas["PESOS-INMEDIATA"] / 365 / 100) * 4
                    if tasa_compra > tasa_caucion:
                        print(colored("\nOportunidad de compra %s - INM: %.2f %.2f - 48HS: %.2f %.2f" % \
                                      (ticker, buy_price, buy_tot, sell_price, sell_tot), "green"))
                        operar(ticker, buy_price, sell_price)
                    else:
                        print(colored("Tasa de caucion mayor a tasa de compra. Caucion: %s - Compra: %s" %
                                      (tasa_caucion, tasa_compra), "red"))
                else:
                    print(colored("No hay liquidez para la venta. Total a la venta: %s" % sell_tot, "red"))
            else:
                print(colored("No hay liquidez para la compra. Total a la compra: %s" % buy_tot, "red"))
        else:
            print(
                colored("No hay oportunidad de discrepancia. Compra: %s - Venta: %s" % (buy_price, sell_price), "red"))
    else:
        print(colored("Una de las puntas no existe. Compra: %s - Venta: %s" % (buy_price, sell_price), "red"))


def main():
    try:
        ppi.account.login('User', 'Password')

        # todo validar feriados
        diasemana = datetime.today().weekday()
        if diasemana == 5 or diasemana == 6:
            print("Fin de semana")
            quit()

        print("Getting accounts information")
        account_numbers = ppi.account.get_accounts()
        for account in account_numbers:
            print(account)
        account_number = account_numbers[0]['accountNumber']

        print("\nGetting available balance of %s" % account_number)
        balances = ppi.account.get_available_balance(account_number)
        for balance in balances:
            if balance['symbol'] == "ARS" and balance['settlement'] == "INMEDIATA":
                amount = balance['amount']
                print("\nSaldo disponible para operar %s" % amount)

        if amount < 20000:
            print("Sin liquidez sobrante")
            quit()

        def onconnect_marketdata():
            try:
                print("\nConnected to realtime market data")

                # todo agregar feriados
                diasemana = datetime.today().weekday()
                if diasemana == 3 or diasemana == 4:
                    tickercaucion = "PESOS4"
                else:
                    tickercaucion = "PESOS2"
                msg = ppi.marketdata.current(SearchMarketData(tickercaucion, "CAUCIONES", "INMEDIATA"))
                puntas["PESOS-INMEDIATA"] = msg['price']
                print("Tasa de caucion en %s %s" % (tickercaucion, puntas["PESOS-INMEDIATA"]))
                ppi.realtime.subscribe_to_element(Instrument(tickercaucion, "CAUCIONES", "INMEDIATA"))

                for ticker in tickers:
                    ppi.realtime.subscribe_to_element(Instrument(ticker, "ACCIONES", "A-48HS"))
                    ppi.realtime.subscribe_to_element(Instrument(ticker, "ACCIONES", "INMEDIATA"))
            except Exception as error:
                traceback.print_exc()

        def ondisconnect_marketdata():
            try:
                print("\nDisconnected from realtime market data")
            except Exception as error:
                traceback.print_exc()

        # Realtime MarketData
        def onmarketdata(data):
            try:
                msg = json.loads(data)

                # La caucion puede estar en diferentes plazos
                if msg['Ticker'].startswith("PESOS"):
                    ticker = "PESOS"
                else:
                    ticker = msg['Ticker']

                if msg["Trade"] == False:
                    # Si es caucion no me importa el libro
                    if ticker != "PESOS":
                        print(msg)
                        plazo = msg['Settlement']

                        if plazo == "INMEDIATA" and len(msg['Offers']) > 0:
                            puntas[ticker + '-' + plazo] = msg['Offers'][0]['Price']

                        if plazo == "A-48HS" and len(msg['Bids']) > 0:
                            puntas[ticker + '-' + plazo] = msg['Bids'][0]['Price']

                        if puntas[ticker + '-A-48HS'] > 0 and puntas[ticker + '-INMEDIATA'] > 0 \
                                and puntas[ticker + '-A-48HS'] > puntas[ticker + '-INMEDIATA']:
                            print(
                                "Detectada posible compra %s Compra: %.2f Venta: %.2f" %
                                (ticker, puntas[ticker + '-INMEDIATA'], puntas[ticker + '-A-48HS']))
                            evaluarPuntas(ticker)
                else:
                    if ticker == "PESOS":
                        print(msg)
                        puntas["PESOS-INMEDIATA"] = msg['Price']
                        # print("Tasa de caucion en %s %s" % (ticker, puntas["PESOS-INMEDIATA"]))

            except Exception as error:
                print(datetime.now())
                print("Error en marketdata: %s. Trace:\n" % error)
                traceback.print_exc()

        ppi.realtime.connect_to_market_data(onconnect_marketdata, ondisconnect_marketdata, onmarketdata)

    except Exception as message:
        print(message)


if __name__ == '__main__':
    main()
