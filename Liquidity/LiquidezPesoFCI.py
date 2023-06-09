### Automatically invest the liquidity of the account in pesos at the end of the day in mutual funds

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
                if balance['symbol']=="ARS" and balance['settlement']=="INMEDIATA":
                    amount = balance['amount']
                    print("\nSaldo disponible para operar %s" % amount)

            if amount > 1000:
                now = datetime.now()
                if now < now.replace(hour=15, minute=45, second=0, microsecond=0):
                    # Get budget
                    print("\nGet budget")
                    budget = ppi.orders.budget(OrderBudget(account_number, amount, 1, "TT.AHORRO.A", "FCI", "Dinero",
                                                           "PRECIO-DE-MERCADO", "HASTA-SU-EJECUCIÓN", None,
                                                           "Suscripción-fci", "INMEDIATA"))
                    print(budget)
                    disclaimers = budget['disclaimers']

                    # Confirm budget
                    print("\nConfirm budget")
                    acceptedDisclaimers = []
                    for disclaimer in disclaimers:
                        acceptedDisclaimers.append(Disclaimer(disclaimer['code'], True))
                    confirmation = ppi.orders.confirm(OrderConfirm(account_number, amount, 1, "TT.AHORRO.A", "FCI",
                                                                   "Dinero", "PRECIO-DE-MERCADO", "HASTA-SU-EJECUCIÓN",
                                                                   None, "Suscripción-fci", "INMEDIATA",
                                                                   acceptedDisclaimers, None))
                    print(confirmation)
                else:
                    print("Suscripcion de FCI ya cerró por el día")
            else:
                print("Sin liquidez sobrante")
        else:
            print("Fin de semana")
    except Exception as message:
        print(message)


if __name__ == '__main__':
    main()

