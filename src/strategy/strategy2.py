# -*- coding: utf-8 -*-

from aioquant.utils import logger
from aioquant.tasks import SingleTask
from aioquant.platform.binance import BinanceRestAPI


class Strategy02:
    """第一个aioquant程序，拉取账户信息、下单、撤单"""

    def __init__(self):
        host = "https://testnet.binance.vision/api" # 币安现货测试
        access_key = "1xknWUXFboKa3LbH3sHNJGUU90jjp4yCQr9tqM3CNMNumVNXTssXNWl2zDiHvksJ" # 币安现货测试key
        secret_key = "boidkxaaA2rbDJOTsfSVGqqXNZTgblHqaxfKBrKi77krtB1f7uwDpAGD4NhIOjoU" # 币安现货测试secret
        self._rest_api = BinanceRestAPI(access_key, secret_key, host=host)

        SingleTask.run(self.get_asset_information)
        # SingleTask.run(self.create_new_order)
        # SingleTask.run(self.revoke_order)

    async def get_asset_information(self):
        """获取账户资产"""
        success, error = await self._rest_api.get_user_account()
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)

    async def create_new_order(self):
        symbol = "BNBUSDT"
        action = "SELL"
        price =  "330"
        quantity = "10"
        success, error = await self._rest_api.create_order(action, symbol, price, quantity)
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)

    async def revoke_order(self):
        """撤销订单"""
        symbol = "BNBUSDT"
        order_id = "95448"
        success, error = await self._rest_api.revoke_order(symbol, order_id)
        logger.info("success:", success, caller=self)
        logger.info("error:", error, caller=self)
