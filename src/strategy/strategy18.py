# -*- coding:utf-8 -*-

"""
k线存储
"""

from aioquant import const
from aioquant.utils import logger
from aioquant.configure import config
from aioquant.market import MarketSubscribe, Kline
from aioquant.data import KLineData


class Strategy18:
    """存储K线"""

    def __init__(self):
        self._platform = config.strategy["platform"]
        self._symbol = config.strategy["symbol"]
        self._db = KLineData(self._platform)

        MarketSubscribe(const.MARKET_TYPE_KLINE, self._platform, self._symbol, self.on_event_kline_update)

    async def on_event_kline_update(self, kline: Kline):
        logger.info("receive kline:", kline, caller=self)
        await self._db.create_new_kline(kline)

