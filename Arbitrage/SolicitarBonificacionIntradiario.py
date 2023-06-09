### Automatically request the bonification of intraday operations to the portfoliopersonal operations area

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
import smtplib
import ssl
from email.mime.text import MIMEText

# Change sandbox variable to False to connect to production environment
ppi = PPI(sandbox=False)


def main():
    try:
        # Change login credential to connect to the API
        ppi.account.login('User', 'Password')

        # Getting accounts information
        print("Getting accounts information")
        account_numbers = ppi.account.get_accounts()
        for account in account_numbers:
            print(account)
        account_number = account_numbers[0]['accountNumber']

        now = datetime.now()
        tomorrow = now.replace(day=now.day + 1, minute=0, second=0, microsecond=0)
        # Get orders
        print("Get orders")
        orders = ppi.orders.get_orders(
            OrdersFilter(from_date=now, to_date=tomorrow,
                         account_number=account_number))

        list = {}
        control = {}
        for order in orders:
            if (order['instrumentType'] == "ACCIONES" or order['instrumentType'] == "BONOS") and (
                    order['status'] == "EJECUTADA" or order['status'] == "EJECUTADA PARCIALMENTE"):
                if order['operation'] == "COMPRA" and order['settlement'] == "INMEDIATA":
                    if order['ticker'] in list:
                        list[order['ticker']] = list[order['ticker']] + order['quantity']
                        control[order['ticker']] = control[order['ticker']] + order['quantity']
                    else:
                        list.update({order['ticker']: order['quantity']})
                        control.update({order['ticker']: order['quantity']})
                else:
                    if order['operation'] == "VENTA" and order['settlement'] == "A-48HS":
                        if order['ticker'] in list:
                            control[order['ticker']] = control[order['ticker']] - order['quantity']

        if len(list) > 0:
            message = """Buenos dias, solicito bonificar intradiario para la cuenta comitente NRO_COMITENTE de las siguientes operaciones de compra en inmediato y venta en 48 horas realizadas en el dia:

            """

            enviar = False
            for inst in list:
                print(inst)

                if control[inst] <= 0:
                    enviar = True
                    # Tanto operaciones completas como parciales con venta completa
                    message = message + ("\nOperadas %.2f para el instrumento %s" % (list[inst], inst))
                elif list[inst] - control[inst] > 0:
                    enviar = True
                    # Esto porque fueron ejecuciones que no se llegó a hacer la venta
                    message = message + ("\nOperadas %.2f para el instrumento %s" % (list[inst] - control[inst], inst))

            port = 465  # For SSL
            smtp_server = "smtp.gmail.com"
            sender_email = "xxx@gmail.com"
            receiver_email = ["xxx@portfoliopersonal.com", "xxx@portfoliopersonal.com"]
            password = "Password"

            print(message)

            if enviar == True:
                msg = MIMEText(message)
                msg['Subject'] = 'Bonificacion intradiario NRO_COMITENTE'
                msg['From'] = sender_email
                msg['To'] = 'xxx@portfoliopersonal.com'

                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_email, msg.as_string())
        else:
            print("No hay operaciones intradiarias")

    except Exception as message:
        print(datetime.now())
        print(message)


if __name__ == '__main__':
    main()

