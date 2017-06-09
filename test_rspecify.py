# -*- coding: utf-8 -*-

pytest_plugins = "pytester"
import pytest

class TestRsoecifiedTerminalReporter(object):

    def setup_method(self, method):
        self.conftest = open("./conftest.py", "r")

    def test_formatting_of_list_of_tests(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            def test_failing_function():
                assert 0

            def test_passing_function():
                assert 1 == 1
            """
        )
        testdir.makeconftest(self.conftest.read())
        result = testdir.runpytest('--rspecify')

        result.stdout.fnmatch_lines([
            "test_formatting_of_list_of_tests*",
            "failing function (FAILED)",
            "passing function (PASSED)"
        ])
