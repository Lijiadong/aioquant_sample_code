# -*- coding:utf-8 -*-

from aioquant.order import Order, ORDER_ACTION_BUY, ORDER_ACTION_SELL
from aioquant.trade import Trade
from aioquant.position import Position
from aioquant import const
from aioquant.error import Error
from aioquant.configure import config
from aioquant.utils import logger
from aioquant.tasks import SingleTask, LoopRunTask


class Strategy14:

    def __init__(self):
        """"""

        params = {
            "strategy": "strategy14",
            "platform": const.BINANCE_FUTURE,
            "symbol": config.symbol,
            "account": config.account,
            "host": config.host,
            "wss": config.wss,
            "access_key": config.access_key,
            "secret_key": config.secret_key,
            "init_callback": self.on_event_init_callback,
            "order_update_callback": self.on_event_order_update_callback,
            "position_update_callback": self.on_event_position_update_callback,
            "error_callback": self.on_event_error_callback,
        }

        self._trade = Trade(**params)
        self._success = False # 初始化状态标志

    def initialize(self):
        """初始化函数"""
        #SingleTask.call_later(self.open_short_position, 10)
        SingleTask.call_later(self.close_short_position, 10)

    async def on_event_init_callback(self, success: bool, **kwargs):
        logger.info("success:", success, caller=self)
        self._success = success

    async def on_event_error_callback(self, error: Error, **kwargs):
        logger.info("error:", error, caller=self)

    async def on_event_order_update_callback(self, order: Order):
        logger.info("order:", order, caller=self)

    async def on_event_position_update_callback(self, position: Position):
        logger.info("position:", position, caller=self)

    async def open_long_position(self):
        if not self._success:
            logger.warn("initialize error!", caller=self)
            return

        action = ORDER_ACTION_BUY
        price = "16935"
        quantity = 0.01
        await self._trade.create_order(action, quantity, price)

    async def close_long_position(self):
        if not self._success:
            logger.warn("initialize error!", caller=self)
            return

        action = ORDER_ACTION_SELL
        price = "16929"
        quantity = 0.01
        await self._trade.create_order(action, quantity, price)

    async def open_short_position(self):
        if not self._success:
            logger.warn("initialize error!", caller=self)
            return

        action = ORDER_ACTION_SELL
        price = "16935"
        quantity = 0.01
        await self._trade.create_order(action, quantity, price)

    async def close_short_position(self):
        if not self._success:
            logger.warn("initialize error!", caller=self)
            return

        action = ORDER_ACTION_BUY
        price = "16929"
        quantity = 0.01
        await self._trade.create_order(action, quantity, price)