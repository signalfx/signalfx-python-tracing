# Copyright (C) 2019 SignalFx. All rights reserved.
import random
import string
import sys

try:  # python 2
    range = xrange
except NameError:
    pass

min_int = -sys.maxsize - 1
max_int = sys.maxsize

_random_int_store = set()
_random_str_store = set()
_random_float_store = set()


def random_int(min=min_int, max=max_int):
    """
    Returns a unique int [min, max], raising Exception if not available.
    Default min is -sys.maxsize - 1 and default max is sys.maxsize.
    """
    if max > max_int or min < min_int:
        raise Exception(
            "random_int(min, max) arguments must be in [{}, {}]".format(
                min_int, max_int
            )
        )

    possibles = []
    # xrange in python 2 requires C long, so surpassing sys.maxsize not possible (i.e. xrange(0, max_int + 1)).
    if max == max_int:
        if max_int not in _random_int_store:
            possibles.append(max_int)

    for i in range(min, max):
        num = random.randint(min, max)
        if num not in _random_int_store:
            _random_int_store.add(num)
            return num
        if i not in _random_int_store:
            possibles.append(i)

    if not possibles:
        raise Exception(
            "Unable to create unique random int in range [{}, {}]".format(min, max)
        )

    num = random.choice(possibles)
    _random_int_store.add(num)
    return num


def random_string():
    while True:
        s = "".join(random.choice(string.ascii_lowercase) for _ in range(10))
        if s not in _random_str_store:
            _random_str_store.add(s)
            return s


def random_float():
    while True:
        i = random.random() * 100000
        if i not in _random_float_store:
            _random_float_store.add(i)
            return i
