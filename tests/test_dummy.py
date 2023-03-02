""" Test suite for dummy module
"""
from clipy import dummy_func


class TestDummy:
    def test_dummy_func_return_1(self):
        assert dummy_func() == 1
