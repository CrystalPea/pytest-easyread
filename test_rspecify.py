# -*- coding: utf-8 -*-

pytest_plugins = "pytester"
import pytest

class TestRspecifiedTerminalReporter(object):

    def setup_method(self, method):
        self.conftest = open("./conftest.py", "r")

    def test_list_of_tests_items_formatted_correctly(self, testdir):
        testdir.makepyfile("""
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
            "test_list_of_tests_items_formatted_correctly*",
            "  failing function (FAILED)",
            "  passing function (PASSED)"
        ])

    def test_list_of_tests_has_empty_line_between_files(self, testdir):
        test_content = """
            import pytest
            def test_failing_function():
                assert 0

            def test_passing_function():
                assert 1 == 1
            """
        testdir.makepyfile(test_list_of_tests=test_content,test_list_of_tests2=test_content)
        testdir.makeconftest(self.conftest.read())
        result = testdir.runpytest('--rspecify')

        expected_result = "\n\ntest_list_of_tests.py \n  failing function (FAILED)\n  passing function (PASSED)\n\ntest_list_of_tests2.py \n  failing function (FAILED)\n  passing function (PASSED)"
        assert expected_result in result.stdout.str()

    def test_class_name_for_tests_formatted_correctly(self, testdir):
        test_content = """
            import pytest
            class TestClassName(object):
                def test_failing_function(self):
                    assert 0

                def test_passing_function(self):
                    assert 1 == 1
            """
        testdir.makepyfile(test_list_of_tests=test_content,test_list_of_tests2=test_content)
        testdir.makeconftest(self.conftest.read())
        result = testdir.runpytest('--rspecify')

        expected_result = "test_list_of_tests.py \n  TestClassName \n    failing function (FAILED)\n    passing function (PASSED)\n\ntest_list_of_tests2.py \n  TestClassName \n    failing function (FAILED)\n    passing function (PASSED)"
        assert expected_result in result.stdout.str()
