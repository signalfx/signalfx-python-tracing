#!/usr/bin/env python
from __future__ import print_function

from argparse import ArgumentParser
import subprocess
import pkgutil
import sys
import os


def is_installed(library):
    return library in sys.modules or pkgutil.find_loader(library) is not None


opentracing = 'opentracing==2.0.0'
jaeger_client = 'https://github.com/signalfx/jaeger-client-python/tarball/ot_20_http_sender#egg=jaeger-client'

instrumenters = {
    'flask': 'https://github.com/signalfx/python-flask/tarball/adopt_scope_manager#egg=flask_opentracing',
    'django': 'https://github.com/signalfx/python-django/tarball/django_2_ot_2_jaeger#egg=django-opentracing',
    'pymongo': 'https://github.com/signalfx/python-pymongo/tarball/master#egg=pymongo-opentracing',
    'pymysql': 'https://github.com/signalfx/python-dbapi/tarball/master#egg=dbapi-opentracing',
    'redis': 'https://github.com/opentracing-contrib/python-redis/tarball/v1.0.0#egg=redis-opentracing',
    'requests': 'https://github.com/signalfx/python-requests/tarball/master#egg=requests-opentracing',
    'tornado': 'tornado_opentracing==1.0.1',
}


if __name__ == '__main__':
    ap = ArgumentParser()
    ap.add_argument('--jaeger', action='store_true')
    args = ap.parse_args()
    cwd = os.path.abspath(os.path.dirname(__file__))

    if args.jaeger:
        print('Installing Jaeger Client.')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', jaeger_client])

    for library, instrumenter in instrumenters.items():
        if is_installed(library):
            print('Installing {} instrumenter.'.format(library))
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', instrumenter])

    print('Installing SignalFx-Tracing.')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-I', opentracing, cwd])
