#!/usr/bin/env python
# Copyright (C) 2018-2019 SignalFx, Inc. All rights reserved.
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages
import sys
import os

version = '0.0.4'


class PyTest(TestCommand):
    user_options = []

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(['tests/unit', '--ignore', 'tests/unit/libraries', '-p', 'no:django']))


def stripped_dependencies(deps):
    """Reduces any pip-friendly vcs/url to package name for setuptools compatibility"""
    return [dep if 'egg=' not in dep else dep.split('egg=')[1] for dep in deps]


def isolated_dependencies(deps):
    """
    Ensures `pip install signalfx-tracing[django,jaeger,redis]` installs desired extras.
    Returns a dictionary of top level package name to amended PEP 508 url with exceedingly high version.
    Should guarantee supported instrumentor versions are installed in
    absence of dependency links: https://github.com/pypa/pip/issues/4187
    """
    isolated = {}
    version_operators = ('>=', '==', '<=', '<', '>')
    for dep in deps:
        dep_name = dep
        set_versioned_dep_name = False
        path_to_split = dep if ',' not in dep else dep.split(',')[0]
        operator_hits = [op in path_to_split for op in version_operators]
        if any(operator_hits):
            dep_name = path_to_split.split(version_operators[operator_hits.index(True)])[0]
            set_versioned_dep_name = True

        dep_pep508 = dep
        if '@' in dep:
            if not set_versioned_dep_name:
                dep_name = dep.split('@')[0].strip()
            dep_pep508 = '{}-999999999'.format(dep)

        isolated[dep_name] = dep_pep508
    return isolated


cwd = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(cwd, 'requirements.txt')) as requirements_file:
    requirements = requirements_file.read().splitlines()

with open(os.path.join(cwd, 'requirements-test.txt')) as test_requirements_file:
    integration_test_requirements = test_requirements_file.read().splitlines()

with open(os.path.join(cwd, 'requirements-inst.txt')) as inst_requirements_file:
    instrumentors = inst_requirements_file.read().splitlines()
    instrumentor_map = isolated_dependencies(instrumentors)

with open(os.path.join(cwd, 'README.md')) as readme_file:
    long_description = readme_file.read()

unit_test_requirements = ['mock', 'pytest', 'six']

setup(name='signalfx-tracing',
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
      ],
      packages=find_packages(),
      install_requires=requirements,
      tests_require=unit_test_requirements,
      extras_require=dict(
          unit_tests=unit_test_requirements,
          instrumentation_tests=integration_test_requirements + list(instrumentor_map.values()),
          # track with extras list in README
          dbapi=instrumentor_map['dbapi-opentracing'],
          django=instrumentor_map['django-opentracing'],
          elasticsearch=instrumentor_map['elasticsearch-opentracing'],
          flask=instrumentor_map['flask_opentracing'],
          jaeger=instrumentor_map['jaeger-client'],
          psycopg2=instrumentor_map['dbapi-opentracing'],
          pymongo=instrumentor_map['pymongo-opentracing'],
          pymysql=instrumentor_map['dbapi-opentracing'],
          redis=instrumentor_map['redis-opentracing'],
          requests=instrumentor_map['requests-opentracing'],
          tornado=instrumentor_map['tornado_opentracing']
      ),
      entry_points=dict(
          console_scripts=[
              'sfx-py-trace = scripts.sfx_py_trace:main',
              'sfx-py-trace-bootstrap = scripts.bootstrap:console_script'
          ]
      ),
      cmdclass=dict(test=PyTest))
