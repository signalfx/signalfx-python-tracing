#!/usr/bin/env python
# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
from setuptools import setup, find_packages

version = '0.0.1'

setup(name='signalfx-tracing',
      version=version,
      author='SignalFx, Inc.',
      author_email='info@signalfx.com',
      description='Provides auto-instrumentation for OpenTracing traced libraries and frameworks',
      license='Apache Software License v2',
      classifiers=[
          'Development Status ::  4 - Beta',
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
      install_requires=[
          'opentracing==2.0.0',
          'wrapt'
      ],
      extras_require={
          'tests': [
              'docker',
              'mock',
              'pytest',
              'six',
          ],
      },
      entry_points={
          'console_scripts': [
              'sfx-py-trace = scripts.sfx_py_trace:main',
              'sfx-py-trace-bootstrap = scripts.bootstrap:console_script'
          ]
      })
