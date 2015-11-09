#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import types
import datetime
import functools
import inspect
from collections import namedtuple

import six

from . import conf, util, core, exceptions


# =============================================================================
# CONSTANTS
# =============================================================================

TEST_MODULE = "{}.test".format(conf.PACKAGE)


# =============================================================================
# CLASSES
# =============================================================================

Call = namedtuple(
    "Call", ["name", "timestamp", "args", "kwargs", "status"])


class CorralAssertWrapper(object):

    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.calls = []

    def collect(self, status, args, kwargs):
        now = datetime.datetime.now()
        call = Call(
            status=status, name=self.name, timestamp=now,
            args=args, kwargs=kwargs)
        self.calls.append(call)

    def __call__(self, *args, **kwargs):
        try:
            self.func(*args, **kwargs)
        except AssertionError:
            self.collect("fail", args, kwargs)
            raise
        except:
            self.collect("error", args, kwargs)
            raise
        else:
            self.collect("pass", args, kwargs)


class CorralTestCaseMeta(abc.ABCMeta):

    @staticmethod
    def __new__(cls, name, parents, dct):
        new = super(CorralTestCaseMeta, cls).__new__(cls, name, parents, dct)

        assert_methods = {}
        for mname in dir(new):
            method = getattr(new, mname)
            is_assert = (mname.startswith("assert") and
                         isinstance(method, types.MethodType))
            if is_assert:
                replacement = CorralAssertWrapper(mname, method)
                wrapped = functools.wraps(method)(replacement)
                setattr(new, mname, wrapped)
                assert_methods[method] = replacement

        new._assert_methods = assert_methods
        return new


@six.add_metaclass(CorralTestCaseMeta)
class CorralTestCase(unittest.TestCase):

    if six.PY2:
        assertCountEqual = six.assertCountEqual

    def scope_process(self):
        scope = self.scope
        if isinstance(scope, run.Loader):
            run.execute_loader(scope)
        elif isinstance(scope, run.Step):
            run.execute_step(scope)
        else:
            msg = ("Scope must be subclass of 'corral.run.Step' "
                   "or 'corral.run.Loader'. Found: '{}'")
            raise exceptions.ImproperlyConfigured(msg.format(scope)

    def runTest(self):
        with db.session_scope() as session, self.scope(session):
            self.setup()
            self.pre_validate()
            self.scope_process()
            self.post_validate()

    def setup(self):
        pass

    @abc.abstractmethod
    def pre_validate(self):
        pass

    @abc.abstractmethod
    def post_validate(self):
        pass


# =============================================================================
# HEAD
# =============================================================================

def load_test_module():
    return util.dimport(TEST_MODULE)


def test_cases_from_module(module):
    for obj in vars(module).values():
        if inspect.isclass(obj) and issubclass(obj, CorralTestCase):
            yield obj


def run_tests(module, verbosity=1, failfast=False):

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    runner = unittest.runner.TextTestRunner(
        verbosity=verbosity, failfast=failfast)

    for case in test_cases_from_module(module):
        tests = loader.loadTestsFromTestCase(case)
        if tests.countTestCases():
            suite.addTests(tests)

    suite_result = runner.run(suite)

    result = suite_result
    return result

