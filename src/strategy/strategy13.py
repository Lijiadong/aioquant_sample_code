# -*- coding: utf-8 -*-
import asyncio

from aioquant.platform.binance import BinanceRestAPI
from aioquant.tasks import LoopRunTask, SingleTask
from aioquant.utils import logger
from aioquant.utils.decorator import async_method_locker
from aioquant.trade import Trade
from aioquant.order import Order, ORDER_STATUS_FILLED, ORDER_STATUS_PARTIAL_FILLED, ORDER_STATUS_FAILED, ORDER_STATUS_CANCELED
from aioquant.const import BINANCE, MARKET_TYPE_ORDERBOOK
from aioquant.error import Error
from aioquant import quant
import asyncio
from aioquant.configure import config
from aioquant.market import Orderbook, MarketSubscribe


class Strategy13:
    """实现动态挂单，将买单价格动态保持在买6和买8之间
    """

    def __init__(self):

        self._rest_api = BinanceRestAPI(config.access_key, config.secret_key)

        self._order_id = None
        self._symbol = 'BNBUSDT'
        self._price = 100
        self._quantity = 0.1
        self._is_ok = True
        self._debut = True

        MarketSubscribe(MARKET_TYPE_ORDERBOOK, BINANCE, config.symbol, self.on_event_orderbook_update)

        params = {
            "strategy": config.strategy,
            "platform": config.platform,
            "host": config.host,
            "wss": config.wss,
            "symbol": config.symbol,
            "account": config.account,
            "access_key": config.access_key,
            "secret_key": config.secret_key,
            "order_update_callback": self.on_order_update_callback,
            "init_callback": self.on_init_callback,
            "error_callback": self.on_error_callback,
        }

        self._trade = Trade(**params)  # TODO: init是放到task里面执行的，所以会和下一条指令产生竞争关系

    async def on_event_orderbook_update(self, orderbook:Orderbook):
        #logger.info("orderbook", orderbook, caller=self)
        bid6 = float(orderbook.bids[5][0])
        bid8 = float(orderbook.bids[7][0])
        await self.process(bid6, bid8)

    @async_method_locker("strategy13.process", wait=True, timeout=5)
    async def process(self, bid6, bid8):
        avg_price = round((bid6 + bid8) / 2, 4)
        logger.info("average price:", avg_price, caller=self)

        if self._order_id and self._price:
            if self._price <= bid6 and self._price >= bid8:
                return
        if self._order_id:
            await self.revoke_order(self._order_id)

        await self.create_order(avg_price)

    async def create_order(self, price):
        action = "BUY"
        quantity = self._quantity
        order_id, error = await self._trade.create_order(action, price, quantity)
        if error:
            return

        self._order_id = order_id
        self._price = price
        logger.info("order_id:", self._order_id, caller=self)

    async def revoke_order(self, order_id):
        success, error = await self._trade.revoke_order(order_id)
        if error:
            return
        logger.info("order_id:", order_id, caller=self)

    async def on_order_update_callback(self, order: Order):
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
            # 报警信息...
            pass
        elif order.status == ORDER_STATUS_CANCELED:
            self._order_id = None
            self._price = None
        else:
            return

    async def on_init_callback(self, success: bool, *args, **kwargs):
        logger.info("success：", success, caller=self)
        if not success:
            return

        self._is_ok = True

    async def on_error_callback(self, error: Error, **kwargs):
        logger.info("error：", error, caller=self)
        self._is_ok = False
        # 发送钉钉消息，打电话报警，或者停止程序
        quant.stop()
