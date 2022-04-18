CONDITIONAL_ORDER = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "price": "",
    "duration": "DAY",
    "orderStrategyType": "TRIGGER",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 0,
            "instrument": {
                "symbol": "",
                "assetType": "EQUITY"
            }
        }
    ],
    "childOrderStrategies": [
        {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": "",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": 0,
                    "instrument": {
                        "symbol": "",
                        "assetType": "EQUITY"
                    }
                }
            ]
        }
    ]
}


if __name__ == "__main__":
    CONDITIONAL_ORDER["price"] = 100
    CONDITIONAL_ORDER["orderLegCollection"][0]["quantity"] = 10
    CONDITIONAL_ORDER["orderLegCollection"][0]["instrument"]["symbol"] = "TSLA"

    CONDITIONAL_ORDER["childOrderStrategies"][0]["price"] = 101
    CONDITIONAL_ORDER["childOrderStrategies"][0]["orderLegCollection"][0]["quantity"] = 100
    CONDITIONAL_ORDER["childOrderStrategies"][0]["orderLegCollection"][0]["instrument"]["symbol"] = "TSLA"
    print(CONDITIONAL_ORDER)
