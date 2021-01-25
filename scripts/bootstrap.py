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


jaeger_client = 'sfx-jaeger-client>=3.13.1b0.dev5'

old_instrumentors = [
    'elasticsearch-opentracing',
    'celery-opentracing',
    'django-opentracing',
    'Flask-Opentracing',
    'dbapi-opentracing',
    'pymongo-opentracing',
    'dbapi-opentracing',
    'redis-opentracing',
    'requests-opentracing',
    'tornado-opentracing',
]

# target library to desired instrumentor path/versioned package name
instrumentors = {
    'celery': 'signalfx-instrumentation-celery>=1.0.0',
    'django': 'signalfx-instrumentation-django>=1.0.0',
    'elasticsearch': 'signalfx-instrumentation-elasticsearch>=1.0.0',
    'flask': 'signalfx-instrumentation-flask>=1.0.0',
    'psycopg2': 'signalfx-instrumentation-dbapi>=1.0.0',
    'pymongo': 'signalfx-instrumentation-pymongo>=1.0.0',
    'pymysql': 'signalfx-instrumentation-dbapi>=1.0.0',
    'redis': 'signalfx-instrumentation-redis>=1.0.0',
    'requests': 'signalfx-instrumentation-requests>=1.0.0',
    'tornado': 'signalfx-instrumentation-tornado>=1.0.0',
}

# relevant instrumentors and tracers to uninstall and check for conflicts for target libraries
packages = {
    'celery': ('signalfx-instrumentation-celery',),
    'django': ('signalfx-instrumentation-django',),
    'elasticsearch': ('signalfx-instrumentation-elasticsearch',),
    'flask': ('signalfx-instrumentation-flask',),
    'jaeger': ('sfx-jaeger-client', 'jaeger-client'),
    'psycopg2': ('signalfx-instrumentation-dbapi',),
    'pymongo': ('signalfx-instrumentation-pymongo',),
    'pymysql': ('signalfx-instrumentation-dbapi',),
    'redis': ('signalfx-instrumentation-redis',),
    'requests': ('signalfx-instrumentation-requests',),
    'signalfx-tracing': ('signalfx-tracing',),
    'tornado': ('signalfx-instrumentation-tornado',),
}


def _to_target_arg(target=None):
    return ['-t', target] if target else []


def _install_or_print_updated_dependency(library, package_path, target=None, print_dep=False):
    if print_dep:
        print(package_path)
    else:
        _install_updated_dependency(library, package_path, target)


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
        for package in old_instrumentors:
            if '{}=='.format(package).lower() in pip_list:
                print('Found deprecated instrumentor {}. Uninstalling.'.format(package))
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


def install_jaeger(target=None, print_deps=False):
    if not print_deps:
        print('Installing Jaeger Client.')
    _install_or_print_updated_dependency('jaeger', jaeger_client, target, print_deps)


def install_deps(target=None, print_deps=False):
    for library, instrumentor in instrumentors.items():
        if is_installed(library):
            if not print_deps:
                print('Installing {} instrumentor.'.format(library))
            _install_or_print_updated_dependency(library, instrumentor, target, print_deps)


def install_sfx_py_trace(target=None):
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    print('Installing SignalFx-Tracing.')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-I', cwd] + _to_target_arg(target))


target_help = ('The value to provide pip for --target: "Install packages into <dir>.". '
               'Will trigger additional signalfx-tracing installation from PyPI to target.')

requirements_help = ('Print the list of packages instead of installing them.')


def console_script():
    ap = ArgumentParser()
    ap.add_argument('-t', '--target', help=target_help)
    ap.add_argument('-r', '--requirements', action='store_true', help=requirements_help)
    args = ap.parse_args()

    if args.target:
        _install_or_print_updated_dependency(
            'signalfx-tracing', 'signalfx-tracing', args.target, args.requirements
        )

    install_jaeger(args.target, args.requirements)
    install_deps(args.target, args.requirements)
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
