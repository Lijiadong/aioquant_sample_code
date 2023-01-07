# -*- coding: utf-8 -*-

from aioquant import quant
from aioquant.MarketPublish import MarketPublish
from aioquant.const import MARKET_TYPE_ORDERBOOK, BINANCE
from aioquant.configure import config

def market():
    print("I'm only do market subscription ...")
    MarketPublish(MARKET_TYPE_ORDERBOOK, BINANCE, config.symbol, config.wss)


if __name__ == "__main__":
    config_file = "../config_market.json"
    quant.start(config_file, market)