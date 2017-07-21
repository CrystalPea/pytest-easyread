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
            class TestSecondClass(object):
                def test_passing_function(self):
                    assert 1 == 1
            """
        testdir.makepyfile(test_list_of_tests=test_content,test_list_of_tests2=test_content)
        testdir.makeconftest(self.conftest.read())
        result = testdir.runpytest('--rspecify')

        expected_result = "test_list_of_tests.py \n  TestClassName \n    failing function (FAILED)\n    passing function (PASSED)\n  TestSecondClass \n    passing function (PASSED)\n\ntest_list_of_tests2.py \n  TestClassName \n    failing function (FAILED)\n    passing function (PASSED)"
        assert expected_result in result.stdout.str()

    def test_failure_titles_have_index_numbers_and_formatting(self, testdir):
        test_content = """
            import pytest
            class TestClassName(object):
                def test_zero_is_truthy(self):
                    assert 0

                def test_passing_function(self):
                    assert 1 == 1

            def test_one_equals_two():
                assert 1 == 2
            """
        testdir.makepyfile(test_list_of_tests=test_content,test_list_of_tests2=test_content)
        testdir.makeconftest(self.conftest.read())
        result = testdir.runpytest('--rspecify')

        result.stdout.fnmatch_lines([
            "1. TestClassName: zero is truthy",
            "2. one equals two",
        ])

    def test_there_are_no_separator_dashes_within_report_messages(self, testdir):
        test_content = """
            import pytest
            from do_not_panic import is_it_answer_to_life_universe_and_everything
            class TestClassName(object):
                def test_is_it_answer_to_life_universe_and_everything_throws_error_if_string_passed_in(self):
                    assert is_it_answer_to_life_universe_and_everything("love") == True
            """

        do_not_panic = """
            def is_it_answer_to_life_universe_and_everything(integer):
                if isinstance(integer, int):
                    return integer == 42
                else:
                    raise NameError("Hint: it's a number! :P")
            """
        testdir.makepyfile(test_list_of_tests=test_content,test_list_of_tests2=test_content, do_not_panic=do_not_panic)
        testdir.makeconftest(self.conftest.read())
        result = testdir.runpytest('--rspecify')
        banished_separator = "_ _ _ _"
        assert banished_separator not in result.stdout.str()
