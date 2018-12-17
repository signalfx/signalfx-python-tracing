#!/usr/bin/env python
from __future__ import print_function

from argparse import ArgumentParser
import subprocess
import pkgutil
import sys
import os


def is_installed(library):
    return library in sys.modules or pkgutil.find_loader(library) is not None


jaeger_client = 'https://github.com/signalfx/jaeger-client-python/tarball/ot_20_http_sender#egg=jaeger-client'

instrumentors = {
    'django': 'https://github.com/signalfx/python-django/tarball/django_2_ot_2_jaeger#egg=django-opentracing',
    'flask': 'https://github.com/signalfx/python-flask/tarball/adopt_scope_manager#egg=flask_opentracing',
    'pymongo': 'pymongo-opentracing',
    'pymysql': 'dbapi-opentracing',
    'redis': 'https://github.com/opentracing-contrib/python-redis/tarball/v1.0.0#egg=redis-opentracing',
    'requests': 'requests-opentracing',
    'tornado': 'tornado_opentracing==1.0.1'
}


def install_jaeger():
    print('Installing Jaeger Client.')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', jaeger_client])


def install_deps():
    for library, instrumentor in instrumentors.items():
        if is_installed(library):
            print('Installing {} instrumentor.'.format(library))
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', instrumentor])


def install_sfx_py_trace():
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    print('Installing SignalFx-Tracing.')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-I', cwd])


def console_script():
    install_jaeger()
    install_deps()


def main():
    ap = ArgumentParser()
    ap.add_argument('--jaeger', action='store_true')
    ap.add_argument('--jaeger-only', action='store_true')
    ap.add_argument('--deps-only', action='store_true')
    args = ap.parse_args()

    if args.jaeger or args.jaeger_only:
        install_jaeger()
        if args.jaeger_only:
            return

    install_deps()

    if not args.deps_only:
        install_sfx_py_trace()


if __name__ == '__main__':
    sys.exit(main())
