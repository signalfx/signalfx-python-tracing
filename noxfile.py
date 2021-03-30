# Copyright (C) 2019 SignalFx. All rights reserved.
import subprocess
import tempfile
import shutil
import os
import re

import nox

pytest = 'pytest<5.0.0'


sdist = None


def build(session):
    global sdist
    if sdist is not None:
        return

    cwd = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(cwd, 'signalfx_tracing/version.py')) as init_file:
        match = re.search("__version__ = ['\"]([^'\"]*)['\"]", init_file.read())
        if not match:
            raise RuntimeError('Not able to determine current version')
    version = match.group(1)

    session.run('python', 'setup.py', 'sdist')
    files = [f for f in os.listdir('dist') if version in f]
    assert len(files) == 1
    sdist = f'dist/{files.pop()}'


def install_unit_tests(session, *other_packages):
    build(session)
    return session.install('attrs==19.1.0', pytest, f'{sdist}[unit_tests]', *other_packages)


def pip_check(session):
    return session.run('pip', 'check')


def pip_freeze(session):
    return session.run('pip', 'freeze')


@nox.session(reuse_venv=True)
def flake8(session):
    session.install('flake8')
    pip_freeze(session)
    session.run('flake8', 'setup.py', 'scripts', 'signalfx_tracing', 'tests', 'noxfile.py')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
def unit(session):
    install_unit_tests(session)
    pip_freeze(session)
    session.run('pytest', 'tests/unit', '--ignore', 'tests/unit/libraries', '-p', 'no:django')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
def bootstrap_with_target(session):
    build(session)
    session.install(sdist)
    dir = tempfile.mkdtemp()
    session.run('sfx-py-trace-bootstrap', '-t', dir)
    target_dir = subprocess.run(['ls', dir], stdout=subprocess.PIPE).stdout.decode()
    assert 'signalfx_tracing' in target_dir
    assert 'jaeger_client' in target_dir
    shutil.rmtree(dir)


# Only testing python versions with full range of celery support.  Other permutations assumed from instrumentation's
# tests until distributed test framework is implemented.
@nox.session(python=('2.7', '3.5', '3.6'), reuse_venv=True)
@nox.parametrize('celery', ('>=3.1,<3.2', '>=4.0,<4.1', '>=4.2,<4.3', '>=4.3,<4.4', '>=4.4.0-rc1,<4.5'))
def celery_via_extras(session, celery):
    install_unit_tests(session, f'celery{celery}')
    session.install(f'{sdist}[celery]')
    pip_check(session)
    pip_freeze(session)
    session.run('pytest', 'tests/unit/libraries/celery_')


def test_django(session):
    session.run('pytest', 'tests/unit/libraries/django_')
    session.run('pytest', 'tests/integration/django_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
def django18_via_bootstrap(session):
    # provides coverage for desired version installation via bootstrap
    install_unit_tests(session, 'django>=1.8,<1.9', 'pytest-django<4.0', 'django-opentracing')
    session.run('sfx-py-trace-bootstrap')
    pip_check(session)
    pip_freeze(session)
    test_django(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('pip', ('<11', '>=18,<19', '>=19,<20'))
def django18_via_extras(session, pip):
    install_unit_tests(session, f'pip{pip}', 'django>=1.8,<1.9', 'pytest-django<4.0')

    django_extra_args = [f'{sdist}[django]']
    if pip == '<11':
        django_extra_args.insert(0, '--process-dependency-links')
    session.install(*django_extra_args)

    pip_check(session)
    pip_freeze(session)
    test_django(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('django', ('>=1.9,<1.10', '>=1.10,<1.11', '>=1.11,<1.12'))
def django19_110_111_via_extras(session, django):
    install_unit_tests(session, f'django{django}', 'pytest-django<4.0')
    session.install(f'{sdist}[django]')
    pip_check(session)
    pip_freeze(session)
    test_django(session)


@nox.session(python=('3.5', '3.6', '3.7'), reuse_venv=True)
def django20_via_extras(session):
    install_unit_tests(session, 'django>=2.0,<2.1', 'pytest-django<4.0')
    session.install(f'{sdist}[django]')
    pip_check(session)
    pip_freeze(session)
    test_django(session)


@nox.session(python=('3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('django', ('>=2.1,<2.2', '>=2.2<2.3'))
def django21_22_via_extras(session, django):
    install_unit_tests(session, f'django{django}', 'pytest-django<4.0')
    session.install(f'{sdist}[django]')
    pip_check(session)
    pip_freeze(session)
    test_django(session)


def test_elasticsearch(session, image_version):
    session.run('pytest', 'tests/unit/libraries/elasticsearch_')
    session.run('pytest', '--elasticsearch-image-version', image_version, 'tests/integration/elasticsearch_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('elasticsearch', ('>=2.0,<2.1', '>=2.1,<2.2', '>=2.2,<2.3', '>=2.3,<2.4', '>=2.4,<2.5'))
def elasticsearch2_via_extras(session, elasticsearch):
    install_unit_tests(session, f'elasticsearch{elasticsearch}', 'docker')
    session.install(f'{sdist}[elasticsearch]')
    pip_check(session)
    pip_freeze(session)
    test_elasticsearch(session, '2.4.6')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('elasticsearch', ('>=5.0,<5.1', '>=5.1,<5.2', '>=5.2,<5.3', '>=5.3,<5.4', '>=5.4,<5.5', '>=5.5,<5.6'))
def elasticsearch5_via_extras(session, elasticsearch):
    install_unit_tests(session, f'elasticsearch{elasticsearch}', 'docker')
    session.install(f'{sdist}[elasticsearch]')
    pip_check(session)
    pip_freeze(session)
    test_elasticsearch(session, '5.6.14')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('elasticsearch', ('>=6.0,<6.1', '>=6.1,<6.2', '>=6.2,<6.3', '>=6.3,<6.4'))
def elasticsearch6i_via_extras(session, elasticsearch):
    install_unit_tests(session, f'elasticsearch{elasticsearch}', 'docker')
    session.install(f'{sdist}[elasticsearch]')
    pip_check(session)
    pip_freeze(session)
    test_elasticsearch(session, '6.5.4')


def test_falcon(session):
    session.run('pytest', 'tests/unit/libraries/falcon_')
    session.run('pytest', 'tests/integration/falcon_')


@nox.session(python=('3.5', '3.6', '3.7'), reuse_venv=True)
def falcon_via_bootstrap(session):
    install_unit_tests(session, 'falcon>=2.0', 'requests')
    session.run('sfx-py-trace-bootstrap')
    pip_check(session)
    pip_freeze(session)
    test_falcon(session)


def test_flask(session):
    session.run('pytest', 'tests/unit/libraries/flask_')
    session.run('pytest', 'tests/integration/flask_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
def flask010_via_bootstrap(session):
    # provides coverage for desired version installation via bootstrap
    install_unit_tests(session, 'flask>=0.10,<0.11', 'requests', 'flask-opentracing')
    session.run('sfx-py-trace-bootstrap')
    pip_check(session)
    pip_freeze(session)
    test_flask(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('pip', ('<11', '>=18,<19', '>=19,<20'))
def flask010_via_extras(session, pip):
    install_unit_tests(session, f'pip{pip}', 'flask>=0.10,<0.11', 'requests')
    flask_extra_args = [f'{sdist}[flask]']
    if pip == '<11':
        flask_extra_args.insert(0, '--process-dependency-links')
    session.install(*flask_extra_args)

    pip_check(session)
    pip_freeze(session)
    test_flask(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('flask', ('>=0.11,<0.12', '>=0.12,<0.13', '>=1.0,<1.1'))
def flask_via_extras(session, flask):
    install_unit_tests(session, f'flask{flask}', 'requests')
    session.install(f'{sdist}[flask]')
    pip_check(session)
    pip_freeze(session)
    test_flask(session)


def test_jaeger(session):
    session.run('pytest', 'tests/integration/test_jaeger_client.py')
    session.run('pytest', 'tests/integration/test_runner.py')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
def jaeger_via_bootstrap(session):
    install_unit_tests(session, 'jaeger-client', 'sfx-jaeger-client')
    session.run('sfx-py-trace-bootstrap')
    pip_check(session)
    pip_freeze(session)
    test_jaeger(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('pip', ('<11', '>=18,<19', '>=19,<20'))
def jaeger_via_extras(session, pip):
    install_unit_tests(session, f'pip{pip}')

    jaeger_extra_args = [f'{sdist}[jaeger,requests]']
    if pip == '<11':
        jaeger_extra_args.insert(0, '--process-dependency-links')
    session.install(*jaeger_extra_args)

    pip_check(session)
    pip_freeze(session)
    test_jaeger(session)


def test_psycopg(session):
    session.run('pytest', 'tests/unit/libraries/psycopg2_')
    session.run('pytest', 'tests/integration/psycopg2_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('psycopg2', ('>=2.7,<2.8', '>=2.8,<2.9'))
def psycopg2_via_extras(session, psycopg2):
    install_unit_tests(session, f'psycopg2{psycopg2}', 'docker')
    session.install(f'{sdist}[psycopg2]')
    test_psycopg(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('psycopg2', ('>=2.7,<2.8', '>=2.8,<2.9'))
def psycopg2_binary_via_extras(session, psycopg2):
    install_unit_tests(session, f'psycopg2-binary{psycopg2}', 'docker')
    session.install(f'{sdist}[psycopg2]')
    test_psycopg(session)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('pymongo', ('>=3.1,<3.2', '>=3.2,<3.3', '>=3.3,<3.4', '>=3.4,<3.5',
                             '>=3.5,<3.6', '>=3.6,<3.7', '>=3.7,<3.8'))
def pymongo_via_extras(session, pymongo):
    install_unit_tests(session, f'pymongo{pymongo}', 'docker', 'mockupdb')
    session.install(f'{sdist}[pymongo]')
    session.run('pytest', 'tests/unit/libraries/pymongo_')
    session.run('pytest', 'tests/integration/pymongo_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('pymysql', ('>=0.8,<0.9', '>=0.9,<0.10'))
def pymysql_via_extras(session, pymysql):
    install_unit_tests(session, f'pymysql{pymysql}', 'docker')
    session.install(f'{sdist}[pymysql]')
    session.run('pytest', 'tests/unit/libraries/pymysql_')
    session.run('pytest', 'tests/integration/pymysql_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('redis', ('>=2.10,<2.11', '>=3.0,<3.1', '>=3.1,<3.2', '>=3.2,<3.3',
                           '>=3.3,<3.4', '>=3.4,<3.5'))
def redis_via_extras(session, redis):
    install_unit_tests(session, f'redis{redis}', 'docker')
    session.install(f'{sdist}[redis]')
    session.run('pytest', 'tests/unit/libraries/redis_')
    session.run('pytest', 'tests/integration/redis_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('requests', ('>=2.0,<2.1', '>=2.10,<2.11', '>=2.11,<2.12', '>=2.12,<2.13',
                              '>=2.13,<2.14', '>=2.14,<2.15', '>=2.15,<2.16', '>=2.16,<2.17',
                              '>=2.17,<2.18', '>=2.18,<2.19', '>=2.19,<2.20', '>=2.20,<2.21',
                              '>=2.21,<2.22', '>=2.1,<2.2', '>=2.2,<2.3', '>=2.3,<2.4',
                              '>=2.4,<2.5', '>=2.5,<2.6', '>=2.6,<2.7', '>=2.7,<2.8',
                              '>=2.8,<2.9', '>=2.9,<2.10'))
def requests_via_extras(session, requests):
    install_unit_tests(session, f'requests{requests}', 'docker')
    session.install(f'{sdist}[requests]')
    session.run('pytest', 'tests/unit/libraries/requests_')
    session.run('pytest', 'tests/integration/requests_')


@nox.session(python=('3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('tornado', ('>=6.0,<7.0'))
def tornado_via_extras(session, tornado):
    _tornado_via_extras(session, tornado)


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
@nox.parametrize('tornado', ('>=4.3,<4.4', '>=4.4,<4.5', '>=4.5,<5.0', '>=5.0,<5.1', '>=5.1,<5.2'))
def tornado_legacy_via_extras(session, tornado):
    _tornado_via_extras(session, tornado)


def _tornado_via_extras(session, tornado):
    install_unit_tests(session, f'tornado{tornado}', 'requests')
    session.install(f'{sdist}[tornado]')
    session.run('pytest', 'tests/unit/libraries/tornado_')
    session.run('pytest', 'tests/integration/tornado_')


@nox.session(python=('2.7', '3.5', '3.6', '3.7'), reuse_venv=True)
def logging(session):
    install_unit_tests(session)
    session.run('sfx-py-trace-bootstrap')
    session.run('pytest', 'tests/unit/libraries/logging_')
