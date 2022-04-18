import time
from contextlib import contextmanager
from dataclasses import dataclass
import pandas as pd
import datetime
import pytz
from datetime import timezone
import json
import urllib
import requests
from splinter import Browser
from ordertypes import CONDITIONAL_ORDER

# user_name = os.environ["user_name"]
# pass_word = os.environ["pass_word"]
# token = os.environ["token"]


@contextmanager
def timeit(name):
    start = time.time()
    yield 
    print(f"{name} took {time.time() - start :.2f}")

class TradingBotException(Exception):
    pass


@dataclass
class AccountInfo:
    account_id: int
    current_cash: float
    buying_power: float
    day_trading_buying_power: float


class TradingBot:
    def __init__(self):
        self._get_auth_code()
        self._get_account_info()
        self.order_status = []

    def _sent_request(self, request_type: str, url: str, params: dict = None) -> requests.Response:
        auth_headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        if not params:
            params = {}
        resp = getattr(requests, request_type)(
            url, headers=auth_headers, **params)
        if resp.status_code != 200:
            print(TradingBotException(resp.status_code, resp.url, resp.json()))

        return resp

    def _get_auth_code(self):
        auth_url = f"https://auth.tdameritrade.com/auth?response_type=code&redirect_uri=https://localhost&client_id={token}%40AMER.OAUTHAP"

        with Browser("chrome", executable_path=r"/usr/local/bin/chromedriver", headless=True) as browser:
            browser.visit(auth_url)
            browser.find_by_id("username0").first.fill(user_name)
            browser.find_by_id("password1").first.fill(pass_word)
            browser.find_by_id("accept").first.click()
            browser.find_by_id("accept").first.click()
            access_code = urllib.parse.unquote(browser.url.split("code=")[1])

        url = "https://api.tdameritrade.com/v1/oauth2/token"
        params = {
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "data": {
                "grant_type": "authorization_code",
                "refresh_token1": "",
                "access_type": "offline",
                "code": access_code,
                "client_id": token,
                "redirect_uri": "https://localhost"
            },
        }
        auth_rep = requests.post(url, **params)

        self.access_token = auth_rep.json()["access_token"]

    def _get_account_info(self):
        account_url = "https://api.tdameritrade.com/v1/accounts"
        content = self._sent_request("get", account_url)
        if content.status_code != 200:
            raise TradingBotException(content.json())

        account_info = content.json()[0]["securitiesAccount"]
        self.account_id = account_info["accountId"]
        self.current_cash = account_info["accountId"]
        self.buying_power = account_info["accountId"]
        self.day_trading_buying_power = account_info["accountId"]

    def send_order(self, params: dict) -> bool:
        order_url = f"https://api.tdameritrade.com/v1/accounts/{self.account_id}/orders"
        CONDITIONAL_ORDER["price"] = params["buy_price"]
        CONDITIONAL_ORDER["orderLegCollection"][0]["quantity"] = params["size"]
        CONDITIONAL_ORDER["orderLegCollection"][0]["instrument"]["symbol"] = params["symbol"]

        CONDITIONAL_ORDER["childOrderStrategies"][0]["price"] = params["sell_price"]
        CONDITIONAL_ORDER["childOrderStrategies"][0]["orderLegCollection"][0]["quantity"] = params["size"]
        CONDITIONAL_ORDER["childOrderStrategies"][0]["orderLegCollection"][0]["instrument"]["symbol"] = params["symbol"]

        res = self._sent_request("post", order_url, {"data": json.dumps(CONDITIONAL_ORDER)})
        print(res)
    
    def _pop_order_status(self, order):
        if "closeTime" not in order:
            status = "cancel"
            closeTime = "NA"
        else:
            status = "filled" if order["quantity"] == order["filledQuantity"] else "pending"
            closeTime = order["closeTime"]
        print(order)
        self.order_status.append(
            {
                "symbol": order["orderLegCollection"][0]["instrument"]["symbol"],
                "quantity": order["quantity"],
                "filledQuantity": order["filledQuantity"],
                "closeTime":  closeTime,
                "enteredTime": order["enteredTime"],
                "price": order["price"],
                "status": status
            }
        )

    def get_today_order(self):

        order_status_url = "https://api.tdameritrade.com/v1/orders"
        today = datetime.date.today().strftime("%Y-%m-%d")
        params = {
            "maxResults": 1000,
            "fromEnteredTime": today,
            "toEnteredTime": today
        }
        
        today_utc = datetime.datetime.today().replace(tzinfo=pytz.UTC)
        res = self._sent_request("get", order_status_url, {"data": params})
        for order in res.json():
            entered_time = datetime.datetime.fromisoformat(order["enteredTime"].replace("+0000", "+00:00")).astimezone(timezone.utc)
            if entered_time.date() >= today_utc.date():
                self._pop_order_status(order)
                if "childOrderStrategies" in order:
                    for child_order in order["childOrderStrategies"]:
                        self._pop_order_status(child_order)
                    
        self.order_df = pd.DataFrame(self.order_status)

    def show_order(self, update=True, only_pending=True):
        if update:
            self.get_today_order()
        
        if only_pending:
            print(self.order_df[self.order_df.status != "filled"])
        else:
            print(self.order_df)
    
    def get_single_order_status(self, order_id):
        single_order_url = f"https://api.tdameritrade.com/v1/accounts/{self.account_id}/orders/{order_id}"
        res = self._sent_request("get", single_order_url)
        res.json()

    def get_history_price(self, symbol):
        price_url = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory"
        params = {
            "apikey": token,
            "periodType": "day",
            "period": 2,
            "frequencyType": "minute",
            "frequency": 1,
            "needExtendedHoursData": False
        }
        res = requests.get(price_url, params=params)

        
        formated_res = []
        for item in res.json()["candles"]:
            formated_res.append(
                {
                    "open": item["open"],
                    "high": item["high"],
                    "low": item["low"],
                    "close": item["close"],
                    "volume": item["volume"],
                    "Date": datetime.datetime.fromtimestamp(item["datetime"] / 1e3),
                }
            )
        df = pd.DataFrame(formated_res)
        print(df.head())
        df.to_csv("tsla.csv", index=False)
        


if __name__ == "__main__":
    td = TradingBot()
    # td.send_order(params={
    #     "buy_price":23.24,
    #     "size":1,
    #     "symbol":"NIO",
    #     "sell_price":23.30,
    # })
    with timeit("second"):
        td.show_order()
