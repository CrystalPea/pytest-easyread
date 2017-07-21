import pytest
from _pytest.terminal import TerminalReporter


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--rspecify', action="store_true", dest="rspecify", default=False,
        help=(
            "make pytest reporting output more readable"
            "default)."
        )
    )

@pytest.mark.trylast
def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave, we are already active on the master
    if config.option.rspecify:
        # Get the standard terminal reporter plugin...
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        rspecify_reporter = RspecifiedTerminalReporter(standard_reporter)

        # ...and replace it with our own rspecifying reporter.
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(rspecify_reporter, 'terminalreporter')


class RspecifiedTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self._tw = reporter._tw
        self.testfiles = []
        self.testclasses = []

    def write_fspath_result(self, nodeid, res, **kwargs):
        # inbuilt pytest reporter method; changes made: added **kwargs to add markup to path name
        fspath = self.config.rootdir.join(nodeid.split("::")[0])
        if fspath != self.currentfspath:
            self.currentfspath = fspath
            fspath = self.startdir.bestrelpath(fspath)
            self._tw.line()
            self._tw.write(fspath + " ", **kwargs)
        self._tw.write(res)

    def write_ensure_prefix(self, prefix, extra="", **kwargs):
        # inbuilt pytest reporter method; changes made: added **kwargs to add markup to titles of tests
        if self.currentfspath != prefix:
            self._tw.line()
            self.currentfspath = prefix
            self._tw.write(prefix, **kwargs)
        if extra:
            self._tw.write(extra, **kwargs)
            self.currentfspath = -2

    def write_path_name(self, nodeid):
        # called from `pytest_runtest_logstart`:
        # responsible for writing bold path name above list of all tests for that file
        pathname = nodeid.split("::")[0]
        if pathname not in self.testfiles:
            self.testclasses = []
            if self.testfiles != []:
                self._tw.line()
            self.testfiles.append(pathname)
            self.write_fspath_result(pathname, "", **({'bold': True}))

    def write_class_name(self, nodeid):
        # called from `pytest_runtest_logstart`:
        # responsible for writing class name above list of all tests for that class
        if len(nodeid.split("::")) >= 3:
            classname = nodeid.split("::")[1]
            if classname not in self.testclasses:
                self.testclasses.append(classname)
                self.write_fspath_result("  " + classname, "")

    def pytest_runtest_logstart(self, nodeid, location):
        # inbuilt pytest reporter method; extended with `write_path_name` and `write_class_name`
        if self.showlongtestinfo:
            line = self._locationline(nodeid, *location)
            self.write_ensure_prefix(line, "")
        elif self.showfspath:
            self.write_path_name(nodeid)
            self.write_class_name(nodeid)

    def get_formatted_test_title(self, report):
        test_title = (report.nodeid.split("::")[-1]).split("_")
        if test_title[0].lower() == "test":
            test_title.pop(0)
        test_title = " ".join(test_title)
        return test_title

    def pytest_runtest_logreport(self, report):
        # inbuilt pytest reporter method; changes made:
        # test_title introduced. It formats test title to make it more readable
        # checking for verbosity is turned off (verbose by default) as this plugin works best for verbose mode.
        # indentation and markup for test title introduced
        rep = report
        test_title = self.get_formatted_test_title(rep)
        test_title += " "
        res = self.config.hook.pytest_report_teststatus(report=rep)
        cat, letter, word = res
        self.stats.setdefault(cat, []).append(rep)
        self._tests_ran = True
        if not letter and not word:
            # probably passed setup/teardown
            return
        # if self.verbosity <= 0:
        #     if not hasattr(rep, 'node') and self.showfspath:
        #         self.write_fspath_result(rep.nodeid, letter)
        #     else:
        #         self._tw.write(letter)
        # else:
        if isinstance(word, tuple):
            word, markup = word
        else:
            if rep.passed:
                markup = {'green':True}
            elif rep.failed:
                markup = {'red':True}
            elif rep.skipped:
                markup = {'yellow':True}
        line = self._locationline(rep.nodeid, *rep.location)
        if not hasattr(rep, 'node'):
            word = "({})".format(word)
            if len(rep.nodeid.split("::")) >= 3:
                indentation = "    "
            else:
                indentation = "  "
            self.write_ensure_prefix(indentation + test_title, word, **markup)
            #self._tw.write(word, **markup)
        else:
            self.ensure_newline()
            if hasattr(rep, 'node'):
                self._tw.write("[%s] " % rep.node.gateway.id)
            self._tw.write(word, **markup)
            self._tw.write(" " + line)
            self.currentfspath = -2

    # Reporting failures
    def get_failure_title(self, rep):
        if len(rep.nodeid.split("::")) >= 3:
            return rep.nodeid.split("::")[1] + ": " + self.get_formatted_test_title(rep)
        else:
             return self.get_formatted_test_title(rep)

    def summary_failures(self):
        if self.config.option.tbstyle != "no":
            reports = self.getreports('failed')
            if not reports:
                return
            self.write_sep(".  ", "FAILURES", **{"bold": True})
            index = 1
            for rep in reports:
                rep.longrepr.reprtraceback.entrysep = ' '
                if self.config.option.tbstyle == "line":
                    line = self._getcrashline(rep)
                    self.write_line(line)
                else:
                    msg = self.get_failure_title(rep)
                    markup = {'red': True, 'bold': True}
                    self.write_ensure_prefix(str(index) + ". " + msg, **markup)
                    index += 1
                    self._outrep_summary(rep)
                    for report in self.getreports(''):
                        if report.nodeid == rep.nodeid and report.when == 'teardown':
                            self.print_teardown_sections(report)
