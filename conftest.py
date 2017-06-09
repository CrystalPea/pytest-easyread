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

    def write_ensure_prefix(self, prefix, extra="", **kwargs):
        if self.currentfspath != prefix:
            self._tw.line()
            self.currentfspath = prefix
            self._tw.write(prefix, **kwargs)
        if extra:
            self._tw.write(extra, **kwargs)
            self.currentfspath = -2

    def pytest_runtest_logstart(self, nodeid, location):
        # ensure that the path is printed before the
        # 1st test of a module starts running
        if self.showlongtestinfo:
            line = self._locationline(nodeid, *location)
            self.write_ensure_prefix(line, "")
        elif self.showfspath:
            fsid = nodeid.split("::")[0]
            if fsid not in self.testfiles:
                self.testfiles.append(fsid)
                self.write_fspath_result(fsid, "")

    def pytest_runtest_logreport(self, report):
        rep = report
        test_title = (report.location[2]).split("_")
        if test_title[0].lower() == "test":
            test_title.pop(0)
        test_title = " ".join(test_title)
        test_title += " "
        res = self.config.hook.pytest_report_teststatus(report=report)
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
            self.write_ensure_prefix(test_title, word, **markup)
            #self._tw.write(word, **markup)
        else:
            self.ensure_newline()
            if hasattr(rep, 'node'):
                self._tw.write("[%s] " % rep.node.gateway.id)
            self._tw.write(word, **markup)
            self._tw.write(" " + line)
            self.currentfspath = -2
