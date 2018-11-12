from argparse import ArgumentParser
import sys
import os

from jaeger_client import Tracer
import opentracing


if __name__ != '__main__':
    raise Exception('Run outside of __main__.')
else:
    assert isinstance(opentracing.tracer, Tracer)

    ap = ArgumentParser()
    ap.add_argument('--one', dest='one', type=int, required=True)
    ap.add_argument('--two', dest='two', type=float)
    ap.add_argument('--three', dest='three', type=str)
    ap.add_argument('-i', dest='i', type=int, nargs='+')
    ap.add_argument('-j', dest='j', type=int, nargs='+')

# Test for sfx_py_tracing collisions
    ap.add_argument('-t', dest='t', type=str)
    ap.add_argument('--token', dest='token', type=str)

    known, unknown = ap.parse_known_args()

    assert known.one == 123
    assert known.two == 123.456
    assert known.three == 'This Is A String'
    assert known.i == [1, 2, 3, 4, 5]
    assert known.j == [1.0, 2.0, 3.0, 4.0, 5.0]

    assert known.t == 'collision1'
    assert known.token == 'collision2'
    assert unknown == ['--unknown=asdf', '-u' 'file.py', 'file.txt']

    assert sys.argv == [os.path.abspath(__file__), '--one', '123', '--two', '123.456',
                        '--three', 'This Is A String', '-i', '1', '2', '3', '4', '5',
                        '-j', '1', '2', '3', '4', '5', '-t', 'collision1', '--token', 'collision2',
                        '--unknown=asdf', '-u' 'file.py', 'file.txt']
