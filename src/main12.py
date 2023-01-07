# -*- coding: utf-8 -*-
import random
import asyncio
from aioquant.tasks import SingleTask
from aioquant.utils.decorator import async_method_locker


@async_method_locker("my_name", wait=False)
async def process_something(index):
    t = random.randrange(1, 10) / 10.0
    await asyncio.sleep(t) # 处理某些工作...
    print("index:", index, "t:", t)

def start():
    for i in range(10):
        SingleTask.run(process_something, i)

start()
asyncio.get_event_loop().run_forever()