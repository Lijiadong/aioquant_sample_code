# -*- coding: utf-8 -*-

from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import SingleTask
from aioquant.utils import logger


class Strategy03:
    """获取订单薄、K线等市场行情信息"""

    def __init__(self):
        host = "https://testnet.binance.vision/api" # 币安现货测试
        access_key = "1xknWUXFboKa3LbH3sHNJGUU90jjp4yCQr9tqM3CNMNumVNXTssXNWl2zDiHvksJ" # 币安现货测试key
        secret_key = "boidkxaaA2rbDJOTsfSVGqqXNZTgblHqaxfKBrKi77krtB1f7uwDpAGD4NhIOjoU" # 币安现货测试secret
        self._rest_api = BinanceRestAPI(access_key, secret_key, host=host)

        # SingleTask.run(self.get_binance_order_book)
        SingleTask.call_later(self.get_binance_order_book, 5)

    async def get_binance_kline(self):
        """获取币安K线数据"""
        symbol = "BNBUSDT"
        # success, error = await self._rest_api.get_latest_ticker(symbol)
        success, error = await self._rest_api.get_kline(symbol, limit=10)
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)

    async def get_binance_trade(self):
        """获取币安逐笔成交"""
        symbol = "BNBUSDT"
        success, error = await self._rest_api.get_trade(symbol, 20)
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)

    async def get_binance_order_book(self):
        """获取币安逐笔成交"""
        symbol = "BNBUSDT"
        success, error = await self._rest_api.get_orderbook(symbol, 20)
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)
