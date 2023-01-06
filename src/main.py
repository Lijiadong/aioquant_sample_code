# -*- coding: utf-8 -*-

from aioquant import quant


def strategy():
    print("I'm here ...")
    from strategy.strategy4 import Strategy04
    Strategy04()


if __name__ == "__main__":
    # config_file = "../config.json"
    config_file = None
    quant.start(config_file, strategy)