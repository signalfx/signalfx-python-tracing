#!/usr/bin/env python
# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
from argparse import ArgumentParser, REMAINDER
import os.path
import sys
import os

from signalfx_tracing import utils

ap = ArgumentParser()
ap.add_argument('--token', '-t', required=False, type=str, dest='token',
                help='Your SignalFx Access Token (SIGNALFX_ACCESS_TOKEN env var by default)')
ap.add_argument('target', help='Your Python application.')
ap.add_argument('target_args', help='Arguments for your application.', nargs=REMAINDER)


def main():
    args = ap.parse_args()
    if args.token:
        os.environ['SIGNALFX_ACCESS_TOKEN'] = args.token

    if utils.is_truthy(os.environ.get('SIGNALFX_TRACING_ENABLED', True)):
        site_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site_')
        py_path = os.environ.get('PYTHONPATH', '')
        os.environ['PYTHONPATH'] = site_dir + os.pathsep + py_path if py_path else site_dir

    # provide the target file as well as follow posix convention
    # that first argv item should be the executable filename
    os.execv(sys.executable, [sys.executable, args.target] + args.target_args)


if __name__ == '__main__':
    main()
