# -*- coding: utf-8 -*-

from aioquant import quant


def entrance():
    print("I'm here ...")
    from strategy.strategy20 import Strategy20
    s = Strategy20()


if __name__ == "__main__":
    config_file = "../config20.json"
    quant.start(config_file, entrance)