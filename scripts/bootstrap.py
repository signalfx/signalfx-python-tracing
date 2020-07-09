#!/usr/bin/env python
# Copyright (C) 2018-2019 SignalFx. All rights reserved.
from __future__ import print_function

from argparse import ArgumentParser
import subprocess
import pkgutil
import sys
import os


def is_installed(library):
    return library in sys.modules or pkgutil.find_loader(library) is not None


jaeger_client = 'sfx-jaeger-client>=3.13.1b0.dev2'


# target library to desired instrumentor path/versioned package name
instrumentors = {
    'celery': 'https://github.com/signalfx/python-celery/tarball/0.0.1post0#egg=celery-opentracing',
    'django': 'https://github.com/signalfx/python-django/tarball/0.1.18post1#egg=django-opentracing',
    'elasticsearch': ('https://github.com/signalfx/python-elasticsearch/tarball/0.1.4post1'
                      '#egg=elasticsearch-opentracing'),
    'flask': 'https://github.com/signalfx/python-flask/tarball/1.1.0post1#egg=flask_opentracing',
    'psycopg2': 'https://github.com/signalfx/python-dbapi/tarball/v0.0.5post0#egg=dbapi-opentracing',
    'pymongo': 'https://github.com/signalfx/python-pymongo/tarball/v0.0.3post1#egg=pymongo-opentracing',
    'pymysql': 'https://github.com/signalfx/python-dbapi/tarball/v0.0.5post0#egg=dbapi-opentracing',
    'redis': 'https://github.com/signalfx/python-redis/tarball/v1.0.0post1#egg=redis-opentracing',
    'requests': 'https://github.com/signalfx/python-requests/archive/v0.2.0post1.zip#egg=requests-opentracing',
    'tornado': 'https://github.com/signalfx/python-tornado/archive/1.0.1post1.zip#egg=tornado_opentracing',
}

# relevant instrumentors and tracers to uninstall and check for conflicts for target libraries
packages = {
    'celery': ('celery-opentracing',),
    'django': ('django-opentracing',),
    'elasticsearch': ('elasticsearch-opentracing',),
    'flask': ('Flask-OpenTracing',),
    'jaeger': ('sfx-jaeger-client', 'jaeger-client'),
    'psycopg2': ('dbapi-opentracing',),
    'pymongo': ('pymongo-opentracing',),
    'pymysql': ('dbapi-opentracing',),
    'redis': ('redis-opentracing',),
    'requests': ('requests-opentracing',),
    'signalfx-tracing': ('signalfx-tracing',),
    'tornado': ('tornado-opentracing',),
}


def _to_target_arg(target=None):
    return ['-t', target] if target else []


def _install_updated_dependency(library, package_path, target=None):
    """
    Ensures that desired version is installed w/o upgrading its dependencies by uninstalling where necessary (if
    `target` is not provided).

    OpenTracing-Contrib often has traced library as instrumentation dependency (e.g. Django for django-opentracing),
    so using -I on library will cause likely undesired Django upgrade.  Using --no-dependencies alone would
    leave potential for nonfunctional installations.
    """
    if not target:
        pip_list = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().lower()
        for package in packages[library]:
            if '{}=='.format(package).lower() in pip_list:
                print('Existing {} installation detected.  Uninstalling.'.format(package))
                subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', package])

    # explicit upgrade strategy to override potential pip config
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U',
                           '--upgrade-strategy', 'only-if-needed', package_path] + _to_target_arg(target))


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
    for package_tup in packages.values():
        for package in package_tup:
            if package.lower() in pip_check_lower:
                raise RuntimeError('Dependency conflict found: {}'.format(pip_check))


def install_jaeger(target=None):
    print('Installing Jaeger Client.')
    _install_updated_dependency('jaeger', jaeger_client, target)


def install_deps(target=None):
    for library, instrumentor in instrumentors.items():
        if is_installed(library):
            print('Installing {} instrumentor.'.format(library))
            _install_updated_dependency(library, instrumentor, target)


def install_sfx_py_trace(target=None):
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    print('Installing SignalFx-Tracing.')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-I', cwd] + _to_target_arg(target))


target_help = ('The value to provide pip for --target: "Install packages into <dir>.". '
               'Will trigger additional signalfx-tracing installation from PyPI to target.')


def console_script():
    ap = ArgumentParser()
    ap.add_argument('-t', '--target', help=target_help)
    args = ap.parse_args()

    if args.target:
        _install_updated_dependency('signalfx-tracing', 'signalfx-tracing', args.target)

    install_jaeger(args.target)
    install_deps(args.target)
    _pip_check()


def main():
    ap = ArgumentParser()
    ap.add_argument('--jaeger', action='store_true')
    ap.add_argument('--jaeger-only', action='store_true')
    ap.add_argument('--deps-only', action='store_true')
    ap.add_argument('-t', '--target', help=target_help)
    args = ap.parse_args()

    if args.jaeger or args.jaeger_only:
        install_jaeger(args.target)
        if args.jaeger_only:
            return

    install_deps(args.target)

    if not args.deps_only:
        install_sfx_py_trace(args.target)


if __name__ == '__main__':
    sys.exit(main())
