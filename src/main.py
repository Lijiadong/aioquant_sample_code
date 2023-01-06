# -*- coding: utf-8 -*-

from aioquant import quant


def strategy():
    print("I'm here ...")
    from strategy.strategy5 import Strategy05
    Strategy05()


if __name__ == "__main__":
    # config_file = "../config.json"
    config_file = None
    quant.start(config_file, strategy)