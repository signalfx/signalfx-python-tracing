#!/usr/bin/env python
# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
from __future__ import print_function

from argparse import ArgumentParser
import subprocess
import pkgutil
import sys
import os


def is_installed(library):
    return library in sys.modules or pkgutil.find_loader(library) is not None


jaeger_client = ('https://github.com/signalfx/jaeger-client-python/tarball/'
                 'ot_20_http_sender_no_tornado#egg=jaeger-client')

instrumentors = {
    'django': 'https://github.com/signalfx/python-django/tarball/django_2_ot_2_jaeger#egg=django-opentracing',
    'elasticsearch': ('https://github.com/signalfx/python-elasticsearch/tarball/2.0_support_multiple_versions'
                      '#egg=elasticsearch-opentracing'),
    'flask': 'https://github.com/signalfx/python-flask/tarball/adopt_scope_manager#egg=flask_opentracing',
    'psycopg2': 'dbapi-opentracing',
    'pymongo': 'pymongo-opentracing',
    'pymysql': 'dbapi-opentracing',
    'redis': 'https://github.com/opentracing-contrib/python-redis/tarball/v1.0.0#egg=redis-opentracing',
    'requests': 'requests-opentracing',
    'tornado': 'tornado-opentracing==1.0.1'
}

packages = {
    'django': 'django-opentracing',
    'elasticsearch': 'elasticsearch-opentracing',
    'flask': 'Flask-OpenTracing',
    'jaeger': 'jaeger-client',
    'psycopg2': 'dbapi-opentracing',
    'pymongo': 'pymongo-opentracing',
    'pymysql': 'dbapi-opentracing',
    'redis': 'redis-opentracing',
    'requests': 'requests-opentracing',
    'signalfx-tracing': 'signalfx-tracing',
    'tornado': 'tornado-opentracing'
}


def _install_updated_dependency(library, package_path):
    """
    Ensures that desired version is installed w/o upgrading its dependencies by uninstalling where necessary.

    OpenTracing-Contrib often has traced library as instrumentation dependency (e.g. Django for django-opentracing),
    so using -I on library will cause likely undesired Django upgrade.  Using --no-dependencies alone would
    leave potential for nonfunctional installations.
    """
    pip_list = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().lower()
    path = packages[library]
    if '{}=='.format(path).lower() in pip_list:
        print('Existing {} installation detected.  Uninstalling.'.format(path))
        subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', path])

    # explicit upgrade strategy to override potential pip config
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U',
                           '--upgrade-strategy', 'only-if-needed', package_path])
    _pip_check()


def _pip_check():
    """Ensures none of the signalfx-tracing instrumentations have dependency conflicts.

    Clean check reported as:
    'No broken requirements found.'

    Dependency conflicts are reported as:
    'django-opentracing 1.0.1 has requirement opentracing<2.1,>=2.0, but you have opentracing 1.3.0.'

    To not be too restrictive, we'll only check for relevant packages.
    """
    check_pipe = subprocess.Popen([sys.executable, '-m', 'pip', 'check'], stdout=subprocess.PIPE)
    pip_check = check_pipe.communicate()[0].decode()
    pip_check_lower = pip_check.lower()
    for package in packages.values():
        if package.lower() in pip_check_lower:
            raise RuntimeError('Dependency conflict found: {}'.format(pip_check))


def install_jaeger():
    print('Installing Jaeger Client.')
    _install_updated_dependency('jaeger', jaeger_client)


def install_deps():
    for library, instrumentor in instrumentors.items():
        if is_installed(library):
            print('Installing {} instrumentor.'.format(library))
            _install_updated_dependency(library, instrumentor)


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
