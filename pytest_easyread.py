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
        easy_reporter = EasyTerminalReporter(standard_reporter)

        # ...and replace it with our own easying reporter.
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(easy_reporter, 'terminalreporter')


class EasyTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self._tw = reporter._tw
        self.testfiles = []
        self.testclasses = []
        self.is_first_failure = True

    def write_fspath_result(self, nodeid, res, **kwargs):
        """
        inbuilt pytest reporter method;
        changes made: added **kwargs to enable adding markup to path name
        """
        fspath = self.config.rootdir.join(nodeid.split("::")[0])
        if fspath != self.currentfspath:
            self.currentfspath = fspath
            fspath = self.startdir.bestrelpath(fspath)
            self._tw.line()
            self._tw.write(fspath + " ", **kwargs)
        self._tw.write(res)

    def write_ensure_prefix(self, prefix, extra="", **kwargs):
        """
        inbuilt pytest reporter method;
        changes made: added **kwargs to enable adding markup to titles of tests
        """
        if self.currentfspath != prefix:
            self._tw.line()
            self.currentfspath = prefix
            self._tw.write(prefix, **kwargs)
        if extra:
            self._tw.write(extra, **kwargs)
            self.currentfspath = -2

    def _write_path_name(self, nodeid):
        pathname = nodeid.split("::")[0]
        if pathname not in self.testfiles:
            self.testclasses = []
            if self.testfiles:
                self._tw.line()
            self.testfiles.append(pathname)
            self.write_fspath_result(pathname, "", **({'bold': True}))

    def _write_class_name(self, nodeid):
        if len(nodeid.split("::")) >= 3:
            classname = nodeid.split("::")[1]
            if classname not in self.testclasses:
                self.testclasses.append(classname)
                self.write_fspath_result(" "*2 + classname, "")

    def pytest_runtest_logstart(self, nodeid, location):
        """
        inbuilt pytest reporter method;
        changes made: extended with _write_path_name() and _write_class_name()
        """
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
            return " "*4
        else:
            return " "*2

    def pytest_runtest_logreport(self, report):
        """
        inbuilt pytest reporter method;
        changes made:
            _get_formatted_test_title() introduced. It formats test title to make it more human-readable;
            _add_indentation_for_tests_list_item() introduced.
            checking for verbosity is turned off (verbose by default) as this plugin works best in verbose mode;
            indentation and markup for test title introduced;
        """
        test_title = self._get_formatted_test_title(report)
        test_title += " "
        res = self.config.hook.pytest_report_teststatus(report=report)
        cat, letter, word = res
        self.stats.setdefault(cat, []).append(report)
        self._tests_ran = True
        if not letter and not word:
            # probably passed setup/teardown
            return
        if isinstance(word, tuple):
            word, markup = word
        else:
            if report.passed:
                markup = {'green':True}
            elif report.failed:
                markup = {'red':True}
            elif report.skipped:
                markup = {'yellow':True}
        line = self._locationline(report.nodeid, *report.location)
        if not hasattr(report, 'node'):
            word = "(%s)" % word
            indentation = self._add_indentation_for_tests_list_item(report)
            self.write_ensure_prefix(indentation + test_title, word, **markup)
        else:
            self.ensure_newline()
            if hasattr(report, 'node'):
                self._tw.write("[%s] " % report.node.gateway.id)
            self._tw.write(word, **markup)
            self._tw.write(" " + line)
            self.currentfspath = -2

    # Functions for reporting failures live below this point
    def _get_failure_title(self, rep):
        if len(rep.nodeid.split("::")) >= 3:
            return rep.nodeid.split("::")[1] + ": " + self._get_formatted_test_title(rep)
        else:
             return self._get_formatted_test_title(rep)

    def _ljust_sep(self, rep, sepchar, title=None, fullwidth=None, **kw):
        """
        based on sep() method of the TerminalWriter's class
        """
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

    def _write_failed_test_title(self, rep, index):
        msg = self._get_failure_title(rep)
        markup = {'red': True, 'bold': True}
        title = str(index) + ". " + msg
        sepchar = " . "
        if not self.is_first_failure:
            self._tw.line()
        self._ljust_sep(rep, sepchar, title, **markup)
        self.is_first_failure = False

    def _write_failed_test_path(self, rep):
        """
        prints the path to the failed test, containing location, class and name of the test;
        :param rep: this is a failed test report (type: object)
        :return: None
        """
        failed_test_path = self._locationline(rep.nodeid, *rep.location)
        self._tw.write(" "*3 + "Path: " + failed_test_path)
        self._tw.line()

    def summary_failures(self):
    """
    inbuilt pytest reporter method;
    changes made:
        change separator for FAILURES heading
        add index numbers for titles of failing tests
        get rid of dashes separating snippets of code from test file and tested file within failure message for a test;
        add an empty line between report printouts for failing tests
        format title of failing test and change separator from an equal sign to a dot surrounded by whitespace
        and move the title from the centre to the left;
        call function that prints the path to the failing test below test title;
    """
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
                    self._write_failed_test_title(rep, index)
                    index += 1
                    self._write_failed_test_path(rep)
                    self._outrep_summary(rep)
                    for report in self.getreports(''):
                        if report.nodeid == rep.nodeid and report.when == 'teardown':
                            self.print_teardown_sections(report)
