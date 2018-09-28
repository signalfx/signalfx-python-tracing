#!/usr/bin/env python
from __future__ import print_function

from argparse import ArgumentParser
import subprocess
import pkgutil
import sys
import os


def is_installed(library):
    return library in sys.modules or pkgutil.find_loader(library) is not None


opentracing = 'https://github.com/signalfx/opentracing-python/tarball/flask_scope_manager#egg=opentracing'
jaeger_client = 'https://github.com/signalfx/jaeger-client-python/tarball/ot_20_http_sender#egg=jaeger-client'

instrumenters = {
    'flask': 'https://github.com/signalfx/python-flask/tarball/use_flask_scope_manager#egg=flask-opentracing',
    'django': 'https://github.com/signalfx/python-django/tarball/django_2_ot_2_jaeger#egg=django-opentracing',
    'pymongo': 'git+ssh://git@github.com/signalfx/python-pymongo.git#egg=pymongo-opentracing',
    'pymysql': 'git+ssh://git@github.com/signalfx/python-dbapi.git#egg=dbapi-opentracing',
    'redis': 'https://github.com/signalfx/python-redis/tarball/ot_v2.0#egg=redis-opentracing',
    'requests': 'git+ssh://git@github.com/signalfx/python-requests.git#egg=requests-opentracing',
    'tornado': 'tornado_opentracing',
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
