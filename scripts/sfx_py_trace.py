#!/usr/bin/env python
# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from argparse import ArgumentParser, REMAINDER
import runpy
import sys
import os

from signalfx_tracing import auto_instrument, create_tracer

ap = ArgumentParser()
ap.add_argument('--token', '-t', required=False, type=str, dest='token',
                help='Your SignalFx Access Token (SIGNALFX_ACCESS_TOKEN env var by default)')
ap.add_argument('target', help='Your Python application.')
ap.add_argument('target_args', help='Arguments for your application.', nargs=REMAINDER)


def main():
    args = ap.parse_args()
    access_token = args.token or os.environ.get('SIGNALFX_ACCESS_TOKEN')

    auto_instrument(create_tracer(access_token=access_token, set_global=True))

    sys.argv = [args.target] + args.target_args
    runpy.run_path(args.target, run_name='__main__')


if __name__ == '__main__':
    main()
