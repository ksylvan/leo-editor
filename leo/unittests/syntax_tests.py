# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20210901140718.1: * @file ../unittests/syntax_tests.py
#@@first
"""Basic tests for Leo"""
# pylint: disable=no-member
import glob
import unittest
from leo.core import leoGlobals as g
from leo.core import leoTest2
#@+others
#@+node:ekr.20210901140855.1: ** class SyntaxTest
class SyntaxTest(unittest.TestCase):
    """Unit tests checking syntax of Leo files."""
    #@+others
    #@+node:ekr.20210901140855.2: *3* SyntaxTest: setUp, tearDown...
    def setUp(self):
        """Create the nodes in the commander."""
        # Must do the import here.
        from leo.core import leoCommands
        # Create a new commander for each test.
        # This is fast, because setUpClass has done all the imports.
        self.c = c = leoCommands.Commands(fileName=None, gui=g.app.gui)
        c.selectPosition(c.rootPosition())
        g.unitTesting = True

    def tearDown(self):
        self.c = None
        g.unitTesting = False

    @classmethod
    def setUpClass(cls):
        leoTest2.create_app()
    #@+node:ekr.20210901140645.1: *3* SyntaxTest.tests...
    #@+node:ekr.20210901140645.21: *4* SyntaxTest.test_syntax_of_all_files
    def test_syntax_of_all_files(self):
        c = self.c
        failed,n = [],0
        skip_tuples = (
            ('extensions','asciidoc.py'),
        )
        join = g.os_path_finalize_join
        skip_list = [join(g.app.loadDir,'..',a,b) for a,b in skip_tuples]
        for theDir in ('core', 'external', 'extensions', 'plugins', 'scripts', 'test'):
            path = g.os_path_finalize_join(g.app.loadDir,'..',theDir)
            assert g.os_path_exists(path),path
            aList = glob.glob(g.os_path_join(path,'*.py'))
            if g.isWindows:
                aList = [z.replace('\\','/') for z in aList]
            for z in aList:
                if z in skip_list:
                    pass # print('%s: skipped: %s' % (p.h,z))
                else:
                    n += 1
                    fn = g.shortFileName(z)
                    s,e = g.readFileIntoString(z)
                    if not c.testManager.checkFileSyntax(fn,s,reraise=False,suppress=False):
                        failed.append(z)
        assert not failed,'failed %s\n' % g.listToString(failed)
    #@+node:ekr.20210901140645.22: *4* SyntaxTest.test_syntax_of_setup_py
    def test_syntax_of_setup_py(self):
        c = self.c
        fn = g.os_path_finalize_join(g.app.loadDir, '..', '..', 'setup.py')
        # Only run this test if setup.py exists: it may not in the actual distribution.
        if g.os_path_exists(fn):
            s, e = g.readFileIntoString(fn)
            c.testManager.checkFileSyntax(fn, s, reraise=True, suppress=False)
    #@-others
#@-others
#@-leo
