### Automatically rescue the liquidity of the account in pesos at the start of the day located in mutual funds

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

        # Getting balance and positions
        print("\nGetting balance and positions of %s" % account_number)
        balances_positions = ppi.account.get_balance_and_positions(account_number)
        for instruments in balances_positions["groupedInstruments"]:
            for instrument in instruments['instruments']:
                print("Instrument %s " % instrument['ticker'])
                if instrument['ticker'] == "TT.AHORRO.A":
                    print(instrument)
                    # Get budget
                    print("\nGet budget")
                    budget = ppi.orders.budget(OrderBudget(account_number, instrument['amount'], instrument['price'], "TT.AHORRO.A", "FCI", "CANTIDAD-TOTAL",
                                                           "PRECIO-DE-MERCADO", "HASTA-SU-EJECUCIÓN", None,
                                                           "Rescate-fci", "INMEDIATA"))
                    print(budget)
                    disclaimers = budget['disclaimers']

                    # Confirm budget
                    print("\nConfirm budget")
                    acceptedDisclaimers = []
                    for disclaimer in disclaimers:
                        acceptedDisclaimers.append(Disclaimer(disclaimer['code'], True))
                    confirmation = ppi.orders.confirm(OrderConfirm(account_number, instrument['amount'], instrument['price'], "TT.AHORRO.A", "FCI",
                                                                   "CANTIDAD-TOTAL", "PRECIO-DE-MERCADO",
                                                                   "HASTA-SU-EJECUCIÓN",
                                                                   None, "Rescate-fci", "INMEDIATA",
                                                                   acceptedDisclaimers, None))
                    print(confirmation)
        else:
            print("Fin de semana")
    except Exception as message:
        print(message)


if __name__ == '__main__':
    main()

