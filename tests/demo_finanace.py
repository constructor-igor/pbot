import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import configuration
from ExchangeRates import ExchangeRates


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting demo ExchangeRates")
    rates = ExchangeRates(configuration.rates_access_token)
    rates = rates.get_rate(base_currency='USD', target_currencies=['ILS', 'EUR'])
    logging.info(f'1 USD = {rates["ILS"]} ILS  / {rates["EUR"]} EUR')
    logging.info(f'1 EUR = {rates["ILS"]/rates["EUR"]} ILS')