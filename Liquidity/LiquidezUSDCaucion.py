### Automatically invest the liquidity of the account in usd at the end of the day in cauciones

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

# Change sandbox variable to False to connect to production environment
ppi = PPI(sandbox=False)


def main():
    try:
        # Change login credential to connect to the API
        ppi.account.login('User', 'Password')

        diasemana = datetime.today().weekday()
        if diasemana != 5 and diasemana != 6:
            # Getting accounts information
            print("Getting accounts information")
            account_numbers = ppi.account.get_accounts()
            for account in account_numbers:
                print(account)
            account_number = account_numbers[0]['accountNumber']

            # Getting available balance
            print("\nGetting available balance of %s" % account_number)
            balances = ppi.account.get_available_balance(account_number)
            for balance in balances:
                if balance['symbol'] == "USD" and balance['settlement'] == "INMEDIATA" and balance[
                            'name'] == "Dolar Billete | MEP":
                    amount = balance['amount']
                    print("\nSaldo disponible para operar %s" % amount)

            if amount > 1000:
                now = datetime.now()
                if now < now.replace(hour=15, minute=45, second=0, microsecond=0):
                    i = 1
                    best_price = 0
                    best_item = ''

                    # Get in the next 14 days
                    for i in range(14):
                        # Search Current Book
                        item = "DOLAR" + str(i + 1)

                        print("Searching Current Book %s" % item)
                        current_book = ppi.marketdata.book(SearchMarketData(item, "CAUCIONES", "INMEDIATA"))
                        print(current_book)
                        if len(current_book['bids']) > 0 and best_price < current_book['bids'][0]['price']:
                            best_price = current_book['bids'][0]['price']
                            best_item = item

                    if best_price > 0:
                        print("\nLa mejor punta compradora es del %s a %.2f" % (best_item, best_price))

                        # Get budget
                        print("\nGet budget")
                        budget = ppi.orders.budget(OrderBudget(account_number, amount, best_price, best_item, "CAUCIONES",
                                                               "Dinero", "PRECIO-LIMITE", "POR-EL-DIA", None,
                                                               "Colocar-caucion", "INMEDIATA"))

                        print(budget)
                        disclaimers = budget['disclaimers']

                        # Confirm budget
                        print("\nConfirm budget")
                        acceptedDisclaimers = []
                        for disclaimer in disclaimers:
                            acceptedDisclaimers.append(Disclaimer(disclaimer['code'], True))
                        confirmation = ppi.orders.confirm(OrderConfirm(account_number, amount, best_price, best_item, "CAUCIONES",
                                                                       "Dinero", "PRECIO-LIMITE", "POR-EL-DIA",
                                                                       None, "Colocar-caucion", "INMEDIATA",
                                                                       acceptedDisclaimers, None))
                        print(confirmation)
                    else:
                        print("No hay punta compradora")
                else:
                    print("El mercado de cauciones ya cerró por el día")
            else:
                print("Sin liquidez sobrante")
        else:
            print("Fin de semana")
    except Exception as message:
        print(message)


if __name__ == '__main__':
    main()

