# -*- coding: utf-8 -*-

from aioquant import quant


def strategy():
    print("I'm here ...")
    from strategy.strategy11 import Strategy11
    Strategy11()


if __name__ == "__main__":
    config_file = "../config11.json"
    quant.start(config_file, strategy)