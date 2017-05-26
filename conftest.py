import pytest

def is_it_answer_to_life_universe_and_everything(integer):
    if isinstance(integer, int):
        return integer == 42
    else:
        raise NameError("Hint: it's a number! :P")

def pytest_report_teststatus(report):
    import sys
    sys.settrace(tracefunc)
    if report.when in ("setup", "teardown"):
        if report.failed:
            return "negative", "NOPE" "INCORRECT"
        elif report.skipped:
            return "skipped", "s", "SKIPPED"
        else:
            return "positive", "SI", "correct"
