# -*- coding: utf-8 -*-

from aioquant import quant


def entrance():
    print("I'm here ...")
    from strategy.strategy14 import Strategy14
    s = Strategy14()
    s.initialize()

if __name__ == "__main__":
    config_file = "../config14.json"
    quant.start(config_file, entrance)