# -*- coding: utf-8 -*-

from aioquant import quant


def entrance():
    print("I'm here ...")
    from strategy.strategy18 import Strategy18
    s = Strategy18()


if __name__ == "__main__":
    config_file = "../config18.json"
    quant.start(config_file, entrance)