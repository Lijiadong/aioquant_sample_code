# -*- coding: utf-8 -*-

from aioquant.utils import logger
from aioquant.tasks import LoopRunTask, SingleTask


class Strategy09:

    def __init__(self):
        self._max_count = 4
        self._task_id = LoopRunTask.register(self.do_something_per_3s_with_something_else, 3, "AIOQuant is awesome!!!")

    async def do_something_per_3s_with_limit(self, text, *args, **kwargs):
        if self._max_count <= 0:
            LoopRunTask.unregister(self._task_id)
            return
        logger.info("I'm doing something...", text, caller=self)
        self._max_count -= 1

    async def do_something_per_3s_with_something_else(self, text, *args, **kwargs):

        logger.info("I'm doing something...", text, caller=self)
        count = kwargs["heart_beat_count"]
        #SingleTask.run(self.do_something_once, count)
        SingleTask.call_later(self.do_something_once, 1, count)

    async def do_something_once(self, count, *args, **kwargs):
        logger.info("total heart beat count:", count, caller=self)