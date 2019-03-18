#!/usr/bin/env python
# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages
import sys
import os
import re


protocols = ('http://', 'https://', 'ssh://', 'svn://')

pep508 = False
try:
    import pip
    # PEP 508 url support was added in pip 18 and dependency link support was
    # dropped in 19: https://github.com/pypa/pip/issues/4187
    if pip.__version__ >= '18.0.0':
        pep508 = True
except ImportError:
    pass


class PyTest(TestCommand):
    user_options = []

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(['tests/unit', '--ignore', 'tests/unit/libraries', '-p', 'no:django']))


class DependencyMap(object):

    def __init__(self, deps):
        """
        Takes a list of dependencies from a requirements file and constructs a dictionary of the form
        {dependency_name: (versioned_dependency_name, dependency_url)} where dependency_url has an
        exceedingly high egg version to ensure preferential installation.

        `self.dep_map`:
        {'requests': ('requests>=1,<2', None),
         'django': (None, 'git+https://github.com/django/django.git@master#egg=django-999999999')}

        Assumes that all deps are not using PEP 508 URL based lookup (e.g. `package @ package_url`),
        though this can be easily constructed from the resulting map w/ `self.map(use_pep508=True)`

        Also assumes all url-based requirements end with `#egg=package_name` or else it is impossible to
        determine the package name without downloading!
        """
        self.dep_map = {}
        version_operators = ('>=', '==', '<=', '<', '>')

        for dep in deps:
            dep_name = dep
            versioned_dep_name = None
            dep_url = None

            if any([proto in dep for proto in protocols]):
                dep_name = dep.split('egg=')[1]
                dep_url = '{}-999999999'.format(dep)
            elif any([op in dep for op in version_operators]):
                # There are multiple hits for complex version constraints (`package>=x,<y`)
                complex_version_dep = dep if ',' not in dep else dep.split(',')[0]
                operator_hits = [op in complex_version_dep for op in version_operators]
                dep_name = complex_version_dep.split(version_operators[operator_hits.index(True)])[0]
                versioned_dep_name = dep

            self.dep_map[dep_name] = (versioned_dep_name, dep_url)

    def map(self, use_pep508=False):
        """
        Constructs a map from `self.dep_map` whose keys are package names and whose values are
        versioned package names or urls.
        if use_pep508 is True, values will be minimal PEP 508 lookup path for installing the desired package:
        {'requests': 'requests',
         'django': 'django>=1.7,<1.8',
         'torndao': 'tornado @ git+https://github.com/tornadoweb/tornado.git@v1.0.0#egg=tornado-999999999'}
        """
        mapped = {}
        for dep_name, dep_tuple in self.dep_map.items():
            versioned_dep_name, dep_url = dep_tuple
            if versioned_dep_name is not None:
                map_url = versioned_dep_name
            elif dep_url is not None:
                map_url = '{} @ {}'.format(dep_name, dep_url) if use_pep508 else dep_url
            else:
                map_url = dep_name
            mapped[dep_name] = map_url
        return mapped


cwd = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(cwd, 'requirements.txt')) as requirements_file:
    requirements = requirements_file.read().splitlines()

with open(os.path.join(cwd, 'requirements-test.txt')) as test_requirements_file:
    integration_test_requirements = test_requirements_file.read().splitlines()

with open(os.path.join(cwd, 'requirements-inst.txt')) as inst_requirements_file:
    instrumentors = inst_requirements_file.read().splitlines()
    instrumentor_dependency_map = DependencyMap(instrumentors)
    instrumentor_map = instrumentor_dependency_map.map(pep508)

with open(os.path.join(cwd, 'README.md')) as readme_file:
    long_description = readme_file.read()

version = None
with open(os.path.join(cwd, 'signalfx_tracing/__init__.py')) as init_file:
    match = re.search("__version__ = ['\"]([^'\"]*)['\"]", init_file.read())
    if not match:
        raise RuntimeError('Not able to determine current version in signalfx_tracing/__init__.py')
    version = match.group(1)


unit_test_requirements = ['mock', 'pytest', 'six']

setup_args = dict(
    name='signalfx-tracing',
    version=version,
    author='SignalFx, Inc.',
    author_email='info@signalfx.com',
    url='http://github.com/signalfx/signalfx-python-tracing',
    download_url='http://github.com/signalfx/signalfx-python-tracing/tarball/master',
    description='Provides auto-instrumentation for OpenTracing-traced libraries and frameworks',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Apache Software License v2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(),
    install_requires=requirements,
    tests_require=unit_test_requirements,
    entry_points=dict(
        console_scripts=[
            'sfx-py-trace = scripts.sfx_py_trace:main',
            'sfx-py-trace-bootstrap = scripts.bootstrap:console_script'
        ]
    ),
    cmdclass=dict(test=PyTest)
)

if not pep508:
    dependency_links = []
    for potential_url in instrumentor_map.values():
        if any([proto in potential_url for proto in protocols]):
            dependency_links.append(potential_url)
    setup_args['dependency_links'] = dependency_links

if pep508:
    instrumentation_test_requirements = integration_test_requirements + list(instrumentor_map.values())
else:
    instrumentation_test_requirements = integration_test_requirements + list(instrumentor_map.keys())


def extras_require(lib):
    return instrumentor_map[lib] if pep508 else lib


setup_args['extras_require'] = dict(
    unit_tests=unit_test_requirements,
    instrumentation_tests=instrumentation_test_requirements,
    dbapi=extras_require('dbapi-opentracing'),
    django=extras_require('django-opentracing'),
    elasticsearch=extras_require('elasticsearch-opentracing'),
    flask=extras_require('flask_opentracing'),
    jaeger=extras_require('jaeger-client'),
    psycopg2=extras_require('dbapi-opentracing'),
    pymongo=extras_require('pymongo-opentracing'),
    pymysql=extras_require('dbapi-opentracing'),
    redis=extras_require('redis-opentracing'),
    requests=extras_require('requests-opentracing'),
    tornado=extras_require('tornado_opentracing')
)

setup(**setup_args)
