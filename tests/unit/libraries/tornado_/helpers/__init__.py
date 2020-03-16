import sys

if sys.version_info >= (3, 3):
    from ._test_case_gen import AsyncHTTPTestCase  # noqa
else:
    from ._test_case import AsyncHTTPTestCase  # noqa
