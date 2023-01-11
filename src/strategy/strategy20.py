# -*- coding:utf-8 -*-

import numpy as np
import pandas as pd
import talib

from aioquant import const
from aioquant.utils.mongo import MongoDBBase
from aioquant.configure import config
from aioquant.market import MarketSubscribe, Kline, Orderbook
from aioquant.position import Position
from aioquant.trade import Trade
from aioquant.order import Order, ORDER_ACTION_BUY, ORDER_ACTION_SELL, ORDER_STATUS_FILLED, ORDER_STATUS_SUBMITTED, ORDER_STATUS_FAILED
from aioquant.asset import Asset
from aioquant.error import Error
from aioquant.utils import logger
from aioquant.utils import tools
from aioquant.utils.telegram import TelegramBot
from aioquant.tasks import LoopRunTask
from aioquant.utils.decorator import async_method_locker

class KlineData:
    """K线数据
    """

    def __init__(self):
        self.db = MongoDBBase(config.kline_data["database"], config.kline_data["collection"])

    async def get_latest_klines(self, count: int = 20):
        """获取最新的k线数据，默认为最近20条"""
        sort = [{"t", -1}]
        datas = await self.db.get_list(sort=sort, limit=count)
        return datas


class Strategy20:
    """
    布林带策略
    """

    def __init__(self):
        """初始化"""
        # 保存最新的20条K线数据
        self._klines = []

        #订阅K线数据
        MarketSubscribe(const.MARKET_TYPE_KLINE, config.strategy["platform"], config.strategy["symbol"], self.on_event_kline_update_callback)

        #订阅盘口数据
        MarketSubscribe(const.MARKET_TYPE_ORDERBOOK, config.strategy["platform"], config.strategy["symbol"], self.on_event_orderbook_update_callback)

        #持仓信息
        self.position = Position()

        # 当前盘口价格
        self.cur_price = None
        self.orderbook = None
        self.orderbook_ok = False
        self.closed_orders = []

        # 初始化Trade交易对象
        params = {
            "strategy": config.strategy["strategy"],
            "platform": config.strategy["platform"],
            "symbol": config.strategy["symbol"],
            "account": config.strategy["account"],
            "host": config.strategy["host"],
            "wss": config.strategy["wss"],
            "access_key": config.strategy["access_key"],
            "secret_key": config.strategy["secret_key"],
            "passphrase": config.strategy["passphrase"],
            "order_update_callback": self.on_event_order_update_callback,
            "position_update_callback": self.on_event_position_update_callback,
            "asset_update_callback": self.on_event_asset_update_callback,
            "init_callback": self.on_event_init_callback,
            "error_callback": self.on_event_error_callback,
        }
        self.trade = Trade(**params)

        # 定时任务
        LoopRunTask.register(self.check_orderbook, interval=60)

    async def on_event_init_callback(self, success: bool, **kwargs):
        """初始化回调"""
        logger.info("initialize status:", success, caller=self)

        """设置杠杆倍数"""
        _, error = await self.trade.set_level(5)
        if error:
            logger.error("set lever error:", error, caller=self)
            success = False

        # 推送telegram提示
        await self.send_strategy_start_message(success)

    async def on_event_error_callback(self, error: Error, **kwargs):
        logger.info("Error:", error, caller=self)
        # 推送钉钉报警

    async def on_event_position_update_callback(self, position: Position):
        """持仓更新回调"""
        # position回调不一定只是本symbol的回调，要检查symbol
        if position.symbol == config.strategy["symbol"]:
            self.position = position
            logger.info("position:", position, caller=self)

    async def on_event_asset_update_callback(self, asset: Asset):
        """资产更新回调"""
        # 平仓时，更新开仓平仓的pnl
        logger.info("asset:", asset, caller=self)

    async def on_event_order_update_callback(self, order: Order):
        """订单更新回调"""
        logger.info("order:", order, caller=self)

        if order.status == ORDER_STATUS_FILLED:
            self.closed_orders.append(order)
            await self.send_order_filled_message(order)
            if self.position.amount == 0:
                await self.calc_pnl()

    async def on_event_orderbook_update_callback(self, orderbook: Orderbook):
        """盘口订单薄数据更新回调"""
        # 取盘口买一卖一最新价格的平均值，作为当前盘口价格
        self.orderbook = orderbook
        self.cur_price = round((float(orderbook.asks[0][0]) + float(orderbook.bids[0][0]))/2, 2)
        #logger.info("cur_price:", self.cur_price, caller=self)

    async def on_event_kline_update_callback(self, kline: Kline):
        """K线数据更新回调"""
        logger.info("kline:", kline, caller=self)

        if not self._klines:
            self._klines = await self.fetch_latest_klines()

        d = {
            "open": kline.open,
            "high": kline.high,
            "low": kline.low,
            "close": kline.close,
            "volume": kline.volume,
            "timestamp": kline.timestamp
        }
        self._klines.append(d)

        # 如果k线条数不够，不做任何事情
        if len(self._klines) < 20:
            logger.warn("k线数量：", len(self._klines), "继续累积K线...")
            return

        # 把多余的数据删除掉，只保留最新的50条K线
        if len(self._klines) > 50:
            self._klines = self._klines[1:]

        # 订单薄未更新
        if not self.orderbook_ok:
            logger.info("orderbook not ok", caller=self)
            return

        df = pd.DataFrame(self._klines)
        df.drop_duplicates("timestamp", inplace=True)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        # 计算boll值
        upper, middle, lower = self.calc_bool(df)
        logger.info("upper:", upper, "middle:", middle, "lower:", lower, caller=self)

        # 方式1：趋势行情（追涨杀跌）
        # 如果当前boll上轨已经大于当前盘口价格，买入开仓
        if upper >= self.cur_price:
            await self.buy_open()
        # 如果当前boll下轨已经小于当前盘口价格，卖出平仓
        if lower <= self.cur_price:
            await self.sell_close()

        # # 方式2：趋势行情
        # # 如果当前boll下轨已经小宇当前盘口价格，卖出开仓
        # if lower <= self.cur_price:
        #     await self.sell_open()
        # # 如果当前boll上轨已经大于当前盘口价格，买入平仓
        # if upper >= self.cur_price:
        #     await self.buy_close()

        # # 方式3： 震荡行情（高抛低吸）
        # # 如果当前boll上轨已经大于当前盘口价格，卖出开仓
        # if upper >= self.cur_price:
        #     await self.sell_open()
        # # 如果当前boll下轨已经小于当前盘口价格，买入平仓
        # if lower <= self.cur_price:
        #     await self.buy_close()

        # # 方式4： 震荡行情
        # # 如果当前boll下轨已经小于当前盘口价格，买入开仓
        # if lower <= self.cur_price:
        #     await self.buy_open()
        # if upper >= self.cur_price:
        #     await self.sell_close()

    @async_method_locker("Strategy20.place_order", wait=True, timeout=5)
    async def check_orderbook(self, *args, **kwargs):
        """检查订单薄是否正常更新"""
        # 1. 检查maker订单薄是否正常
        # 2. 检查taker订单薄是否正常
        # 3. 如果超过一定时间有异常，那么撤单
        elapse = tools.get_cur_timestamp_ms() - self.orderbook.timestamp
        if elapse >= 5 * 1000: # 超过5秒没有更新，撤单
            self.orderbook_ok = False
            logger.info("check orderbook error: {elapse}s not update".format(elapse=elapse//1000))
            success, error = await self.trade.revoke_order()
            if error:
                logger.error("error:", error, caller=self)
            return
        self.orderbook_ok = True
        logger.info("cur_price:", self.cur_price, caller=self)

    def calc_bool(self, df: pd.DataFrame):
        """计算最新的布林值"""
        close = np.array(df["close"].values, dtype="f8")
        upper, middle, lower = talib.BBANDS(
            close,
            timeperiod=5,
            nbdevup=2,
            nbdevdn=2,
            matype=0,
        )
        return upper[-1], middle[-1], lower[-1]

    async def fetch_latest_klines(self):
        """获取最近的20条K线数据"""
        # 创建K线数据库对象
        kline_db = KlineData()
        datas = await kline_db.get_latest_klines(20)
        klines = []
        for data in datas:
            d = {
                "open": data["o"],
                "high": data["h"],
                "low": data["l"],
                "close": data["c"],
                "volume": data["v"],
                "timestamp": data["t"]
            }
            klines.append(d)

        # 确保kline的时效性，过滤最近20分钟内的k线
        start = tools.get_cur_timestamp_ms() - 20 * 60 * 1000
        klines = list(filter(lambda x: x["timestamp"] > start, klines))

        return klines

    @async_method_locker("Strategy20.place_order", wait=True, timeout=5)
    async def buy_open(self):
        """入场：站上boll上轨后开多"""
        # 如果当前已经开仓，那么什么都不做
        if self.position.amount != 0:
            return

        action = ORDER_ACTION_BUY
        price = round(self.cur_price * (1 + 0.01),1) # 超过盘口1%的价格买入,市价买入了
        quantity = config.strategy["quantity"]
        order_id, error = await self.trade.create_order(action, quantity, price)
        if error:
            logger.error("buy open error:", error, caller=self)
            return
        logger.info("buy open success, order_id:", order_id, caller=self)

    @async_method_locker("Strategy20.place_order", wait=True, timeout=5)
    async def sell_open(self):
        """入场：跌破boll下轨开空"""
        # 如果当前已经开仓，那么什么也不做
        if self.position.amount != 0:
            return

        action = ORDER_ACTION_SELL
        price = round(self.cur_price * (1 - 0.01), 1)
        quantity = config.strategy["quantity"]
        order_id, error = await self.trade.create_order(action, quantity, price )
        if error:
            logger.error("buy open error:", error, caller=self)
            return
        logger.info("sell open success, order_id:", order_id, caller=self)

    @async_method_locker("Strategy20.place_order", wait=True, timeout=5)
    async def sell_close(self):
        """出场：多单跌破ma5平多 或 亏损到2%也平多"""
        # 如果当前未开仓， 那么什么都不做
        if self.position.amount <= 0:
            return

        action = ORDER_ACTION_SELL
        price = round(self.cur_price * (1 - 0.01), 2)
        quantity = config.strategy["quantity"]
        order_id, error = await self.trade.create_order(action, quantity, price)
        if error:
            logger.error("sell close error:", error, caller=self)
            return
        logger.info("sell close success, order_id:", order_id, caller=self)

    @async_method_locker("Strategy20.place_order", wait=True, timeout=5)
    async def buy_close(self):
        """出场：空单站上ma5平空 或 亏损到2%也平空"""
        # 如果当前未开仓，那么什么也不做
        if self.position.amount >= 0:
            return

        action = ORDER_ACTION_BUY
        price = round(self.cur_price * (1 + 0.01),1)
        quantity = config.strategy["quantity"]
        order_id, error = await self.trade.create_order(action, quantity, price )
        if error:
            logger.error("buy close error:", error, caller=self)
            return
        logger.info("buy close success, order_id:", order_id, caller=self)

    async def send_strategy_start_message(self, success:bool):
        content = "【策略启动状态：{success}】\n " \
                  "策略：{strategy}\n" \
                  "平台：{platform}\n" \
                  "账户：{account}\n" \
                  "币种：{symbol}\n" \
                  "时间：{dt}".format(
            success="成功" if success else "失败",
            strategy=config.strategy["strategy"],
            platform=config.strategy["platform"],
            account=config.strategy["account"],
            symbol=config.strategy["symbol"],
            dt=tools.ts_to_datetime_str()
        )
        await TelegramBot.send_text_msg(config.telegram["token"], config.telegram["chat_id"], content)

    async def send_order_filled_message(self, order:Order):
        content = "【订单成交】\n" \
                  "策略：{strategy}\n" \
                  "平台：{platform}\n" \
                  "账户：{account}\n" \
                  "币种：{symbol}\n" \
                  "方向：{side}\n" \
                  "价格：{price}\n" \
                  "均价：{avg_price}\n" \
                  "数量：{quantity}\n" \
                  "时间：{dt}".format(
            strategy=config.strategy["strategy"],
            platform=config.strategy["platform"],
            account=config.strategy["account"],
            symbol=config.strategy["symbol"],
            side=order.action,
            price=order.price,
            avg_price=order.avg_price,
            quantity=order.quantity,
            dt=tools.ts_to_datetime_str()
        )
        await TelegramBot.send_text_msg(config.telegram["token"], config.telegram["chat_id"], content)

    async def calc_pnl(self):
        """计算策略损益"""
        pnl = 0.
        for order in self.closed_orders:
            sign = -1 if order.action == ORDER_ACTION_BUY else 1
            pnl += order.avg_price * order.quantity * sign

        content = "【累积收益】\n" \
                  "策略：{strategy}\n" \
                  "平台：{platform}\n" \
                  "账户：{account}\n" \
                  "币种：{symbol}\n" \
                  "笔数：{quantity}\n" \
                  "收益：{pnl}\n" \
                  "时间：{dt}".format(
            strategy=config.strategy["strategy"],
            platform=config.strategy["platform"],
            account=config.strategy["account"],
            symbol=config.strategy["symbol"],
            quantity=len(self.closed_orders),
            pnl=pnl,
            dt=tools.ts_to_datetime_str()
        )
        await TelegramBot.send_text_msg(config.telegram["token"], config.telegram["chat_id"], content)
