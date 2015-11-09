#!/usr/bin/env python
# -*- coding: utf-8 -*-


from corral.qa import CorralTestCase

from . import load


class LoaderTest(CorralTestCase):

    scope = load.Load

    def pre_validate(self):
        pass

    def post_validate(self):
        pass





