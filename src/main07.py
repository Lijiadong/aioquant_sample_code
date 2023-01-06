# -*- coding: utf-8 -*-

from aioquant import quant


def strategy():
    print("I'm here ...")
    from strategy.strategy7 import Strategy07
    Strategy07()


if __name__ == "__main__":
    config_file = "../config07.json"
    quant.start(config_file, strategy)