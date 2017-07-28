import pytest
from _pytest.terminal import TerminalReporter


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--easy', action="store_true", dest="easy", default=False,
        help=(
            "make pytest reporting output more readable"
            "default)."
        )
    )


@pytest.mark.trylast
def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return  # xdist slave, we are already active on the master
    if config.option.easy:
        # Get the standard terminal reporter plugin...
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        easy_reporter = RspecifiedTerminalReporter(standard_reporter)

        # ...and replace it with our own easying reporter.
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(easy_reporter, 'terminalreporter')


class RspecifiedTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self._tw = reporter._tw
        self.testfiles = []
        self.testclasses = []
        self.is_first_failure = True

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

    def _write_path_name(self, nodeid):
        # called from `pytest_runtest_logstart`:
        # responsible for writing bold path name above list of all tests for that file
        pathname = nodeid.split("::")[0]
        if pathname not in self.testfiles:
            self.testclasses = []
            if self.testfiles != []:
                self._tw.line()
            self.testfiles.append(pathname)
            self.write_fspath_result(pathname, "", **({'bold': True}))

    def _write_class_name(self, nodeid):
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
            self._write_path_name(nodeid)
            self._write_class_name(nodeid)

    def _get_formatted_test_title(self, report):
        test_title = (report.nodeid.split("::")[-1]).split("_")
        if test_title[0].lower() == "test":
            test_title.pop(0)
        test_title = " ".join(test_title)
        return test_title

    def _add_indentation_for_tests_list_item(self, report):
        if len(report.nodeid.split("::")) >= 3:
            return "    "
        else:
            return "  "

    def pytest_runtest_logreport(self, report):
        # inbuilt pytest reporter method; changes made:
        # get_formatted_test_title() introduced. It formats test title to make it more readable
        # checking for verbosity is turned off (verbose by default) as this plugin works best for verbose mode.
        # indentation and markup for test title introduced
        rep = report
        test_title = self._get_formatted_test_title(rep)
        test_title += " "
        res = self.config.hook.pytest_report_teststatus(report=rep)
        cat, letter, word = res
        self.stats.setdefault(cat, []).append(rep)
        self._tests_ran = True
        if not letter and not word:
            # probably passed setup/teardown
            return
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
            indentation = self._add_indentation_for_tests_list_item(rep)
            self.write_ensure_prefix(indentation + test_title, word, **markup)
        else:
            self.ensure_newline()
            if hasattr(rep, 'node'):
                self._tw.write("[%s] " % rep.node.gateway.id)
            self._tw.write(word, **markup)
            self._tw.write(" " + line)
            self.currentfspath = -2

    # Reporting failures
    def _get_failure_title(self, rep):
        if len(rep.nodeid.split("::")) >= 3:
            return rep.nodeid.split("::")[1] + ": " + self._get_formatted_test_title(rep)
        else:
             return self._get_formatted_test_title(rep)

    #based on `sep` method of the TerminalWriter's class
    def _ljust_sep(self, rep, sepchar, title=None, fullwidth=None, **kw):
        self._tw.line()
        if fullwidth is None:
            fullwidth = self._tw.fullwidth
        if title is not None:
            N = (fullwidth - len(title) - 2) // len(sepchar)
            fill = sepchar * N
            line = "%s %s" % (title, fill)
        else:
            line = sepchar * (fullwidth // len(sepchar))
        if len(line) + len(sepchar.rstrip()) <= fullwidth:
            line += sepchar.rstrip()
        self._tw.line(line, **kw)

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
                    msg = self._get_failure_title(rep)
                    markup = {'red': True, 'bold': True}
                    title = str(index) + ". " + msg
                    sepchar = " . "
                    if self.is_first_failure == False:
                        self._tw.line()
                    self._ljust_sep(rep, sepchar, title, **markup)
                    self.is_first_failure = False
                    index += 1
                    self._outrep_summary(rep)
                    for report in self.getreports(''):
                        if report.nodeid == rep.nodeid and report.when == 'teardown':
                            self.print_teardown_sections(report)
