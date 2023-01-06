# -*- coding: utf-8 -*-

from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import LoopRunTask, SingleTask
from aioquant.utils import logger


class Strategy04:
    """实现动态挂单，将买单价格动态保持在买6和买8之间
        未处理订单成交、下单/撤单失败的情况
    """

    def __init__(self):
        host = "https://testnet.binance.vision/api" # 币安现货测试
        access_key = "1xknWUXFboKa3LbH3sHNJGUU90jjp4yCQr9tqM3CNMNumVNXTssXNWl2zDiHvksJ" # 币安现货测试key
        secret_key = "boidkxaaA2rbDJOTsfSVGqqXNZTgblHqaxfKBrKi77krtB1f7uwDpAGD4NhIOjoU" # 币安现货测试secret
        self._rest_api = BinanceRestAPI(access_key, secret_key, host=host)

        self._order_id = None
        self._symbol = 'BNBUSDT'
        self._price = 100
        self._quantity = 0.1

        #LoopRunTask.register(self.create_binance_order, 2)
        LoopRunTask.register(self.get_binance_order_book, 2)

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

    async def get_binance_order_book(self, *args, **kwargs):
        success, error = await self._rest_api.get_orderbook(self._symbol, 10)
        logger.info("success:", success, caller=self)
        bid6 = float(success["bids"][5][0])
        bid8 = float(success["bids"][7][0])
        avg_price = round((bid6 + bid8)/2, 2)
        logger.info("average price:", avg_price, caller=self)

        if self._order_id and self._price:
            if self._price <= bid6 and self._price >= bid8:
                return
        if self._order_id:
            await self.revoke_binance_order(self._order_id)

        await self.create_binance_order(avg_price)

    async def create_binance_order(self, price):
        action = "BUY"
        symbol = self._symbol
        quantity = self._quantity
        success, error = await self._rest_api.create_order(action, symbol, price, quantity)
        self._order_id = str(success["orderId"])
        self._price = price
        logger.info("order_id:", self._order_id, caller=self)

    async def revoke_binance_order(self, order_id):
        await self._rest_api.revoke_order(self._symbol, order_id)
        logger.info("order_id:", order_id, caller=self)

    async def get_binance_order_list(self):
        success, error = await self._rest_api.get_all_orders(self._symbol)
