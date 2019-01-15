# Copyright (C) 2019 SignalFx, Inc. All rights reserved.
import random
import sys

min_int = -sys.maxsize - 1
max_int = sys.maxsize

_random_int_store = set()

try:  # python 2
    range = xrange
except NameError:
    pass


def random_int(min=min_int, max=max_int):
    """
    Returns a unique int [min, max], raising Exception if not available.
    Default min is -sys.maxsize - 1 and default max is sys.maxsize.
    """
    for _ in range(min, max):
        num = random.randint(min, max)
        if num not in _random_int_store:
            _random_int_store.add(num)
            return num
    raise Exception('Unable to create unique random int in range [{}, {}]'.format(min, max))
