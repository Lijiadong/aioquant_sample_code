# -*- coding:utf-8 -*-

from aioquant.configure import config
from aioquant.utils.dingtalk import Ding
from aioquant.tasks import LoopRunTask
from aioquant.utils.telegram import TelegramBot


class Strategy19:

    def __init__(self):
        LoopRunTask.register(self.send_warning_message, 5)

    async def send_warning_message(self, *args, **kwargs):
        """推送报警信息"""
        content = "币安行情丢失, 尝试报警"
        #Ding.send_text(content)
        await TelegramBot.send_text_msg(config.telegram["token"], config.telegram["chat_id"], content)


