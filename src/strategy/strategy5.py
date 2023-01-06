# -*- coding: utf-8 -*-

from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import LoopRunTask, SingleTask
from aioquant.utils import logger
from aioquant.trade import Trade
from aioquant.order import Order, ORDER_STATUS_FILLED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FAILED
from aioquant.const import BINANCE
from aioquant.error import Error
from aioquant import quant

class Strategy05:
    """实现动态挂单，将买单价格动态保持在买6和买8之间
        未处理订单成交、下单/撤单失败的情况
    """

    def __init__(self):
        host = "https://testnet.binance.vision/api"  # 币安现货测试
        access_key = "1xknWUXFboKa3LbH3sHNJGUU90jjp4yCQr9tqM3CNMNumVNXTssXNWl2zDiHvksJ"  # 币安现货测试key
        secret_key = "boidkxaaA2rbDJOTsfSVGqqXNZTgblHqaxfKBrKi77krtB1f7uwDpAGD4NhIOjoU"  # 币安现货测试secret
        self._rest_api = BinanceRestAPI(access_key, secret_key, host=host)

        self._order_id = None
        self._symbol = 'BNBUSDT'
        self._price = 100
        self._quantity = 0.1
        self._is_ok = True

        params = {
            "strategy": "strategy05",
            "platform": BINANCE,
            "symbol": "BNB/USDT",
            "host": host, # testnet必须手动录入host
            "wss": "wss://testnet.binance.vision", # testnet必须手动录入wss
            "account": "sample@gmail.com",
            "access_key": access_key,
            "secret_key": secret_key,
            "order_update_callback": self.order_update_callback,
            "init_callback": self.on_init_callback,
            "error_callback": self.on_error_callback,
        }

        self.trade = Trade(**params)

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
        if not self._is_ok:
            logger.warn("Something error...", caller=self)
            quant.stop()
        success, error = await self._rest_api.get_orderbook(self._symbol, 10)
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)
        if error:
            # 推送一条报警消息： 钉钉、微信、电话
            # 接入风控系统:自动判断问题，做出反应
            self._is_ok = False
            return

        bid6 = float(success["bids"][5][0])
        bid8 = float(success["bids"][7][0])
        avg_price = round((bid6 + bid8)/2, 4)
        logger.info("average price:", avg_price, caller=self)

        if self._order_id and self._price:
            if self._price <= bid6 and self._price >= bid8:
                return
        if self._order_id:
            await self.revoke_binance_order(self._order_id)

        await self.create_binance_order(avg_price)

    async def create_binance_order(self, price):

        action = "BUY"
        quantity = self._quantity
        order_id, error = await self.trade.create_order(action, price, quantity)
        if error:
            return

        self._order_id = order_id
        self._price = price
        logger.info("order_id:", self._order_id, caller=self)

    async def revoke_binance_order(self, order_id):

        success, error = await self.trade.revoke_order(order_id)

        if error:
            return

        logger.info("order_id:", order_id, caller=self)

    async def get_binance_order_list(self):
        success, error = await self._rest_api.get_all_orders(self._symbol)

    async def order_update_callback(self, order:Order):
        logger.info("order：", order, caller=self)
        if order.status == ORDER_STATUS_FILLED:
            # 完成对冲
            self._order_id = None
            self._price = None
            pass
        elif order.status == ORDER_STATUS_PARTIAL_FILLED:
            # 部分对冲
            pass
        elif order.status == ORDER_STATUS_FAILED:
            # 报警信息
            pass
        else:
            return

    async def on_init_callback(self, success: bool, **kwargs):
        logger.info("success：", success, caller=self)

    async def on_error_callback(self, error: Error, **kwargs):
        logger.info("error：", error, caller=self)
        self._is_ok = error
        # 发送钉钉消息，打电话报警，或者停止程序
        quant.stop()