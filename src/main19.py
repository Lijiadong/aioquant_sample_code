# -*- coding: utf-8 -*-

from aioquant import quant


def entrance():
    print("I'm here ...")
    from strategy.strategy19 import Strategy19
    s = Strategy19()

if __name__ == "__main__":
    config_file = "../config19.json"
    quant.start(config_file, entrance)