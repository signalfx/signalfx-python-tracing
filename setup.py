#!/usr/bin/env python
# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages
import sys
import os

version = '0.0.1'


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
    """Ensures `pip install --process-dependency-links signalfx-tracing[django,jaeger,redis]` installs desired extras"""
    # Takes advantage of limitation of pip and setuptools dependency links.
    # Should guarantee supported instrumentor version is installed.
    # https://github.com/pypa/pip/issues/3610#issuecomment-356687173
    isolated = []
    for dep in deps:
        if 'https' in dep:
            isolated.append('git+{}-999999999'.format(dep))
    return isolated


cwd = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(cwd, 'requirements.txt')) as requirements_file:
    requirements = requirements_file.read().splitlines()

with open(os.path.join(cwd, 'requirements-test.txt')) as test_requirements_file:
    integration_test_requirements = test_requirements_file.read().splitlines()

with open(os.path.join(cwd, 'requirements-inst.txt')) as inst_requirements_file:
    instrumentors = inst_requirements_file.read().splitlines()
    instrumentation_requirements = stripped_dependencies(instrumentors)
    dependency_links = isolated_dependencies(instrumentors)

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
      dependency_links=dependency_links,
      extras_require=dict(
          unit_tests=unit_test_requirements,
          instrumentation_tests=integration_test_requirements + instrumentation_requirements,
          # track with extras list in README
          dbapi='dbapi-opentracing',
          django='django-opentracing',
          flask='flask_opentracing',
          jaeger='jaeger-client',
          pymongo='pymongo-opentracing',
          pymysql='dbapi-opentracing',
          redis='redis-opentracing',
          requests='requests-opentracing',
          tornado='tornado-opentracing>=1.0.1',
      ),
      entry_points=dict(
          console_scripts=[
              'sfx-py-trace = scripts.sfx_py_trace:main',
              'sfx-py-trace-bootstrap = scripts.bootstrap:console_script'
          ]
      ),
      cmdclass=dict(test=PyTest))
