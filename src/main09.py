# -*- coding: utf-8 -*-

from aioquant import quant


def strategy():
    print("I'm here ...")
    from strategy.strategy9 import Strategy09
    Strategy09()


if __name__ == "__main__":
    config_file = "../config09.json"
    quant.start(config_file, strategy)