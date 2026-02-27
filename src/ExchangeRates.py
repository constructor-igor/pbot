import requests
import logging


class ExchangeRates:
    def __init__(self, access_token):
        self.url = 'https://openexchangerates.org/api/latest.json'
        self.access_token = access_token
        # self.base_currency = 'USD' # 'EUR
        # self.target_currency = 'ILS'
        # self.currency = currency
        # self.rate = rate
    def get_rate(self, base_currency: str='USD', target_currencies=['ILS', 'EUR']):
        symbols = ','.join(target_currencies)
        response = requests.get(f'{self.url}?app_id={self.access_token}&base={base_currency}&symbols={symbols}')
        if response.status_code == 200:
            data = response.json()
            exchange_rates = data['rates']
            return exchange_rates
        else:
            logging.warning(f'Failed to retrieve the exchange rate (code={response.status_code}).')
    def get_bitcoin_usd(self) -> float | None:
        """Returns current Bitcoin price in USD via CoinGecko (free, no API key)."""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': 'bitcoin', 'vs_currencies': 'usd'},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()['bitcoin']['usd']
            else:
                logging.warning(f'CoinGecko request failed (code={response.status_code}).')
                return None
        except Exception as e:
            logging.warning(f'Failed to get Bitcoin price: {e}')
            return None
