# Copyright (C) 2019 SignalFx, Inc. All rights reserved.


def pytest_addoption(parser):
    parser.addoption('--elasticsearch-image-version', action='store', default='6.5.4')
