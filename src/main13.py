# -*- coding: utf-8 -*-

from aioquant import quant


def strategy():
    print("I'm here ...")
    from strategy.strategy13 import Strategy13
    Strategy13()


if __name__ == "__main__":
    config_file = "../config13.json"
    quant.start(config_file, strategy)