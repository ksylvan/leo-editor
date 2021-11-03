# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20210901172411.1: * @file ../unittests/core/test_leoAtFile.py
#@@first
"""Tests of leoAtFile.py"""
import os
import tempfile
import textwrap
from leo.core import leoGlobals as g
from leo.core import leoAtFile
from leo.core import leoBridge
from leo.core.leoTest2 import LeoUnitTest

#@+others
#@+node:ekr.20210901172446.1: ** class TestAtFile(LeoUnitTest)
class TestAtFile(LeoUnitTest):
    """Test cases for leoAtFile.py"""
    #@+others
    #@+node:ekr.20200204095726.1: *3*  TestAtFile.bridge
    def bridge(self):
        """Return an instance of Leo's bridge."""
        return leoBridge.controller(gui='nullGui',
            loadPlugins=False,
            readSettings=False,
            silent=True,
            verbose=False,
        )
    #@+node:ekr.20210901140645.13: *3* TestAtFile.test_at_checkPythonSyntax
    def test_at_checkPythonSyntax(self):
        c, p = self.c, self.c.p
        at = c.atFileCommands
        s = textwrap.dedent('''\
    # no error
    def spam():
        pass
        ''')
        assert at.checkPythonSyntax(p, s), 'fail 1'

        s2 = textwrap.dedent('''\
    # syntax error
    def spam:  # missing parens.
        pass
        ''')

        assert not at.checkPythonSyntax(p, s2, supress=True), 'fail2'

        if not g.unitTesting:  # A hand test of at.syntaxError
            at.checkPythonSyntax(p, s2)
    #@+node:ekr.20210905052021.19: *3* TestAtFile.test_at_directiveKind4
    def test_at_directiveKind4(self):
        c = self.c
        at = c.atFileCommands
        at.language = 'python'  # Usually set by atFile read/write logic.
        table = [
            ('@=', 0, at.noDirective),
            ('@', 0, at.atDirective),
            ('@ ', 0, at.atDirective),
            ('@\t', 0, at.atDirective),
            ('@\n', 0, at.atDirective),
            ('@all', 0, at.allDirective),
            ('    @all', 4, at.allDirective),
            ("@c", 0, at.cDirective),
            ("@code", 0, at.codeDirective),
            ("@doc", 0, at.docDirective),
            ('@others', 0, at.othersDirective),
            ('    @others', 4, at.othersDirective),
            # ("@end_raw", 0, at.endRawDirective), # #2276.
            # ("@raw", 0, at.rawDirective), # #2276.
        ]
        for name in g.globalDirectiveList:
            # Note: entries in g.globalDirectiveList do not start with '@'
            if name not in ('all', 'c', 'code', 'doc', 'end_raw', 'others', 'raw',):
                table.append(('@' + name, 0, at.miscDirective),)
        for s, i, expected in table:
            result = at.directiveKind4(s, i)
            self.assertEqual(result, expected, msg=f"i: {i}, s: {s!r}")
    #@+node:ekr.20210905052021.20: *3* TestAtFile.test_at_directiveKind4_new
    def test_at_directiveKind4_new(self):
        c = self.c
        at = c.atFileCommands
        at.language = 'python'  # Usually set by atFile read/write logic.
        table = (
            (at.othersDirective, '@others'),
            (at.othersDirective, '@others\n'),
            (at.othersDirective, '    @others'),
            (at.miscDirective, '@tabwidth -4'),
            (at.miscDirective, '@tabwidth -4\n'),
            (at.miscDirective, '@encoding'),
            (at.noDirective, '@encoding.setter'),
            (at.noDirective, '@encoding("abc")'),
            (at.noDirective, 'encoding = "abc"'),
            (at.noDirective, '@directive'),  # A crucial new test.
        )
        for expected, s in table:
            result = at.directiveKind4(s, 0)
            self.assertEqual(expected, result, msg=repr(s))
    #@+node:ekr.20210920165831.1: *3* TestAtFile.test_at_doc_part
    def test_at_doc_part(self):
        
        # From leoBeautify.py.
        # The following text *does* survive round-tripping.
        # However, the actual text in leoBeautify.py
        # (In the @doc part of the node cpp.tokenize & helper) does *not* survive.
        s = textwrap.dedent("""\
            @ The following could be added to the 'else' clause::
            # Accumulate everything else.
            while (
                j < n and
                not s[j].isspace() and
                not s[j].isalpha() and
                not s[j] in '"\'_@' and
                    # start of strings, identifiers, and single-character tokens.
                not g.match(s,j,'//') and
                not g.match(s,j,'/*') and
                not g.match(s,j,'-->')
            ):
                j += 1
        """)
        assert s
    #@+node:ekr.20210905052021.21: *3* TestAtFile.test_at_get_setPathUa
    def test_at_get_setPathUa(self):
        c = self.c
        p = c.p
        at = c.atFileCommands
        at.setPathUa(p, 'abc')
        d = p.v.tempAttributes
        d2 = d.get('read-path')
        val1 = d2.get('path')
        val2 = at.getPathUa(p)
        table = (
            ('d2.get', val1),
            ('at.getPathUa', val2),
        )
        for kind, val in table:
            self.assertEqual(val, 'abc', msg=kind)
    #@+node:ekr.20210905052021.23: *3* TestAtFile.test_at_parseLeoSentinel
    def test_at_parseLeoSentinel(self):
        c = self.c
        at = c.atFileCommands  # self is a dummy argument.
        table = (
            # start, end, new_df, isThin, encoding
            # pre 4.2 formats...
            ('#', '', False, True, 'utf-8', '#@+leo-thin-encoding=utf-8.'),
            ('#', '', False, False, 'utf-8', '#@+leo-encoding=utf-8.'),
            # 4.2 formats...
            ('#', '', True, True, 'utf-8', '#@+leo-ver=4-thin-encoding=utf-8,.'),
            ('/*', '*/', True, True, 'utf-8', r'\*@+leo-ver=5-thin-encoding=utf-8,.*/'),
            ('#', '', True, True, 'utf-8', '#@+leo-ver=5-thin'),
            ('#', '', True, True, 'utf-16', '#@+leo-ver=5-thin-encoding=utf-16,.'),
        )
        try:
            for start, end, new_df, isThin, encoding, s in table:
                valid, new_df2, start2, end2, isThin2 = at.parseLeoSentinel(s)
                # g.trace('start',start,'end',repr(end),'len(s)',len(s))
                assert valid, s
                self.assertEqual(new_df, new_df2, msg=repr(s))
                self.assertEqual(isThin, isThin2, msg=repr(s))
                self.assertEqual(end, end2, msg=repr(s))
                self.assertEqual(at.encoding, encoding, msg=repr(s))
        finally:
            at.encoding = 'utf-8'
    #@+node:ekr.20210905052021.24: *3* TestAtFile.test_at_remove
    def test_at_remove(self):
        c = self.c
        at = c.atFileCommands
        exists = g.os_path_exists

        path = g.os_path_join(g.app.testDir, 'xyzzy')
        if exists(path):
            os.remove(path)

        assert not exists(path)
        assert not at.remove(path)

        f = open(path, 'w')
        f.write('test')
        f.close()

        assert exists(path)
        assert at.remove(path)
        assert not exists(path)
    #@+node:ekr.20210905052021.25: *3* TestAtFile.test_at_replaceFile_different_contents
    def test_at_replaceFile_different_contents(self):
        c = self.c
        at = c.atFileCommands
        # Duplicate init logic...
        at.initCommonIvars()
        at.scanAllDirectives(c.p)
        encoding = 'utf-8'
        try:
            # https://stackoverflow.com/questions/23212435
            f = tempfile.NamedTemporaryFile(delete=False, encoding=encoding, mode='w')
            fn = f.name
            contents = 'test contents'
            val = at.replaceFile(contents, encoding, fn, at.root)
            assert val, val
        finally:
            f.close()
            os.unlink(f.name)
    #@+node:ekr.20210905052021.26: *3* TestAtFile.test_at_replaceFile_no_target_file
    def test_at_replaceFile_no_target_file(self):
        c = self.c
        at = c.atFileCommands
        # Duplicate init logic...
        at.initCommonIvars()
        at.scanAllDirectives(c.p)
        encoding = 'utf-8'
        at.outputFileName = None  # The point of this test, but I'm not sure it matters.
        try:
            # https://stackoverflow.com/questions/23212435
            f = tempfile.NamedTemporaryFile(delete=False, encoding=encoding, mode='w')
            fn = f.name
            contents = 'test contents'
            val = at.replaceFile(contents, encoding, fn, at.root)
            assert val, val
        finally:
            f.close()
            os.unlink(f.name)
    #@+node:ekr.20210905052021.27: *3* TestAtFile.test_at_replaceFile_same_contents
    def test_at_replaceFile_same_contents(self):
        c = self.c
        at = c.atFileCommands
        # Duplicate init logic...
        at.initCommonIvars()
        at.scanAllDirectives(c.p)
        encoding = 'utf-8'
        try:
            # https://stackoverflow.com/questions/23212435
            f = tempfile.NamedTemporaryFile(delete=False, encoding=encoding, mode='w')
            fn = f.name
            contents = 'test contents'
            f.write(contents)
            f.flush()
            val = at.replaceFile(contents, encoding, fn, at.root)
            assert not val, val
        finally:
            f.close()
            os.unlink(f.name)
    #@+node:ekr.20210905052021.28: *3* TestAtFile.test_at_scanAllDirectives
    def test_at_scanAllDirectives(self):
        c = self.c
        d = c.atFileCommands.scanAllDirectives(c.p)
        # These are the commander defaults, without any settings.
        self.assertEqual(d.get('language'), 'python')
        self.assertEqual(d.get('tabwidth'), -4)
        self.assertEqual(d.get('pagewidth'), 132)
    #@+node:ekr.20210905052021.29: *3* TestAtFile.test_at_scanAllDirectives_minimal_
    def test_at_scanAllDirectives_minimal_(self):
        c = self.c
        d = c.atFileCommands.scanAllDirectives(c.p)
        assert d
    #@+node:ekr.20210901140645.14: *3* TestAtFile.test_at_tabNannyNode
    def test_at_tabNannyNode(self):
        c, p = self.c, self.c.p
        at = c.atFileCommands
        # Test 1.
        s = textwrap.dedent("""\
            # no error
            def spam():
                pass
        """)
        at.tabNannyNode(p, body=s)
        # Test 2.
        s2 = textwrap.dedent("""\
            # syntax error
            def spam:
                pass
              a = 2
        """)
        try:
            at.tabNannyNode(p, body=s2)
        except IndentationError:
            pass
    #@+node:ekr.20200204094139.1: *3* TestAtFile.test_bug_1469
    def test_bug_1469(self):
        # Test #1469: saves renaming an external file
        # Create a new outline with @file node and save it
        bridge = self.bridge()
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = f"{temp_dir}{os.sep}test_file.leo"
            c = bridge.openLeoFile(filename)
            p = c.rootPosition()
            p.h = '@file 1'
            p.b = 'b1'
            c.save()
            # Rename the @file node and save
            p1 = c.rootPosition()
            p1.h = "@file 1_renamed"
            c.save()
            # Remove the original "@file 1" from the disk
            external_filename = f"{temp_dir}{os.sep}1"
            assert os.path.exists(external_filename)
            os.remove(external_filename)
            assert not os.path.exists(external_filename)
            # Change the @file contents, save and reopen the outline
            p1.b = "b_1_changed"
            c.save()
            c.close()
            c = bridge.openLeoFile(c.fileName())
            p1 = c.rootPosition()
            self.assertEqual(p1.h, "@file 1_renamed")
    #@+node:ekr.20210421035527.1: *3* TestAtFile.test_bug_1889
    def test_bug_1889(self):
        """
        Test #1889: Honor ~ in ancestor @path nodes.
        """
        # Create a new outline with @file node and save it
        bridge = self.bridge()
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = f"{temp_dir}{os.sep}test_file.leo"
            c = bridge.openLeoFile(filename)
            root = c.rootPosition()
            root.h = '@path ~/sub-directory/'
            child = root.insertAsLastChild()
            child.h = '@file test_bug_1889.py'
            child.b = '@language python\n# test #1889'
            path = g.fullPath(c, child)
            assert '~' not in path, repr(path)
    #@+node:ekr.20211102110237.1: *3* TestAtFile.test_put_body_adjacent_at_doc_part
    def test_put_body_adjacent_at_doc_part(self):
        
        c = self.c
        at = leoAtFile.AtFile(c)
        root = c.rootPosition()
        root.h = '@file test.html'
        contents = textwrap.dedent('''\
            @doc
            First @doc part
            @doc
            Second @doc part
        ''')
        expected = textwrap.dedent('''\
            <!--@+doc-->
            <!--
            First @doc part
            -->
            <!--@+doc-->
            <!--
            Second @doc part
            -->
        ''')
        root.b = contents
        at.initWriteIvars(root)
        at.putBody(root)
        result = ''.join(at.outputList)
        self.assertEqual(result, expected)
    #@+node:ekr.20211102110833.1: *3* TestAtFile.test_put_body_at_all
    def test_put_body_at_all(self):
        
        c = self.c
        at = leoAtFile.AtFile(c)
        root = c.rootPosition()
        root.h = '@file test.py'
        child = root.insertAsLastChild()
        child.h = 'child'
        child.b = textwrap.dedent('''\
            def spam():
                pass
                
            @ A single-line doc part.''')
        child.v.fileIndex = '<GNX>'
        contents = textwrap.dedent('''\
            ATall
        ''').replace('AT', '@')
        expected = textwrap.dedent('''\
            #AT+all
            #AT+node:<GNX>: ** child
            def spam():
                pass
                
            @ A single-line doc part.
            #AT-all
        ''').replace('AT', '@')
        root.b = contents
        at.initWriteIvars(root)
        at.putBody(root)
        result = ''.join(at.outputList)
        self.assertEqual(result, expected)
    #@+node:ekr.20211102111413.1: *3* TestAtFile.test_put_body_at_all_after_at_doc
    def test_put_body_at_all_after_at_doc(self):
        
        c = self.c
        at = leoAtFile.AtFile(c)
        root = c.rootPosition()
        root.h = '@file test.py'
        contents = textwrap.dedent('''\
            ATdoc
            doc line 1
            ATall
        ''').replace('AT', '@')
        expected = textwrap.dedent('''\
            #AT+doc
            # doc line 1
            # ATall
        ''').replace('AT', '@')
        root.b = contents
        at.initWriteIvars(root)
        at.putBody(root)
        result = ''.join(at.outputList)
        self.assertEqual(result, expected)
    #@+node:ekr.20211102150707.1: *3* TestAtFile.test_put_body_at_others
    def test_put_body_at_others(self):
        
        c = self.c
        at = leoAtFile.AtFile(c)
        root = c.rootPosition()
        root.h = '@file test_put_body_at_others.py'
        child = root.insertAsLastChild()
        child.h = 'child'
        child.b = '@others\n'
        child.v.fileIndex = '<GNX>'
        contents = textwrap.dedent('''\
            ATothers
        ''').replace('AT', '@')
        expected = textwrap.dedent('''\
            #AT+others
            #AT+node:<GNX>: ** child
            #AT+others
            #AT-others
            #AT-others
        ''').replace('AT', '@')
        root.b = contents
        at.initWriteIvars(root)
        at.putBody(root)
        result = ''.join(at.outputList)
        self.assertEqual(result, expected)
    #@+node:ekr.20211102102024.1: *3* TestAtFile.test_put_body_unterminated_at_doc_part
    def test_put_body_unterminated_at_doc_part(self):
        
        c = self.c
        at = leoAtFile.AtFile(c)
        root = c.rootPosition()
        root.h = '@file test.html'
        contents = textwrap.dedent('''\
            @doc
            Unterminated @doc parts (not an error)
        ''')
        expected = textwrap.dedent('''\
            <!--@+doc-->
            <!--
            Unterminated @doc parts (not an error)
            -->
        ''')
        root.b = contents
        at.initWriteIvars(root)
        at.putBody(root)
        result = ''.join(at.outputList)
        self.assertEqual(result, expected)
    #@-others
#@+node:ekr.20211031085414.1: ** class TestFastAtRead(LeoUnitTest)
class TestFastAtRead(LeoUnitTest):
    """Test the FastAtRead class."""
    #@+others
    #@+node:ekr.20211031085620.1: *3*  TestFast.setUp
    def setUp(self):
        super().setUp()
        self.x = leoAtFile.FastAtRead(self.c, gnx2vnode={})

    #@+node:ekr.20211031093209.1: *3* TestFast.test_at_section_delim
    def test_at_section_delim(self):

        c, x = self.c, self.x
        h = '@file /test/section_delims_test.py'
        root = c.rootPosition()
        root.h =  h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101050923.1: *4* << define contents >>
        # The contents of a personal test file, slightly altered.
        contents = textwrap.dedent(f'''\
        # -*- coding: utf-8 -*-
        #AT+leo-ver=5-thin
        #AT+node:ekr.20211029054120.1: * {h}
        #AT@first

        """Classes to read and write @file nodes."""

        #AT@section-delims <!< >!>

        #AT+<!< test >!>
        #AT+node:ekr.20211029054238.1: ** <!< test >!>
        print('in test section')
        print('done')
        #AT-<!< test >!>

        #AT+others
        #AT+node:ekr.20211030052810.1: ** spam
        def spam():
        pass
        #AT+node:ekr.20211030053502.1: ** eggs
        def eggs():
        pass
        #AT-others

        #AT@language python
        #AT-leo
        ''').replace('#AT', '#@')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
        child1 = root.firstChild()
        child2 = child1.next()
        child3 = child2.next()
        table = (
            (child1, '<!< test >!>'),
            (child2, 'spam'),
            (child3, 'eggs'),
        )
        for child, h in table:
            self.assertEqual(child.h, h)
    #@+node:ekr.20211101085019.1: *3* TestFast.test_at_comment
    def test_at_comment(self):

        c, x = self.c, self.x
        h = '@file /test/test_at_comment.txt'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101090447.1: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        !!! -*- coding: utf-8 -*-
        !!!AT+leo-ver=5-thin
        !!!AT+node:ekr.20211101090015.1: * {h}
        !!!AT@first

        """Classes to read and write @file nodes."""

        !!!AT@comment !!!

        !!!AT+LB test >>
        !!!AT+node:ekr.20211101090015.2: ** LB test >>
        print('in test section')
        print('done')
        !!!AT-LB test >>

        !!!AT+others
        !!!AT+node:ekr.20211101090015.3: ** spam
        def spam():
            pass
        !!!AT+node:ekr.20211101090015.4: ** eggs
        def eggs():
            pass
        !!!AT-others

        !!!AT@language plain
        !!!AT-leo
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
        child1 = root.firstChild()
        child2 = child1.next()
        child3 = child2.next()
        table = (
            (child1, g.angleBrackets(' test ')),
            (child2, 'spam'),
            (child3, 'eggs'),
        )
        for child, h in table:
            self.assertEqual(child.h, h)
    #@+node:ekr.20211101111636.1: *3* TestFast.test_at_delims
    def test_at_delims(self):
        c, x = self.c, self.x
        h = '@file /test/test_at_delims.txt'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101111652.1: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        !! -*- coding: utf-8 -*-
        #AT+leo-ver=5-thin
        #AT+node:ekr.20211101111409.1: * {h}
        #AT@first

        #ATdelims !! 

        !!AT+LB test >>
        !!AT+node:ekr.20211101111409.2: ** LB test >>
        print('in test section')
        print('done')
        !!AT-LB test >>

        !!AT+others
        !!AT+node:ekr.20211101111409.3: ** spam
        def spam():
            pass
        !!AT+node:ekr.20211101111409.4: ** eggs
        def eggs():
            pass
        !!AT-others

        !!AT@language python
        !!AT-leo
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
        child1 = root.firstChild()
        child2 = child1.next()
        child3 = child2.next()
        table = (
            (child1, g.angleBrackets(' test ')),
            (child2, 'spam'),
            (child3, 'eggs'),
        )
        for child, h in table:
            self.assertEqual(child.h, h)
    #@+node:ekr.20211103092228.1: *3* TestFast.test_at_others
    def test_at_others(self):
        
        # In particular, we want to test indented @others.
        c, x = self.c, self.x
        h = '@file /test/test_at_others'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211103092228.2: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        #AT+leo-ver=5-thin
        #AT+node:ekr.20211103092338.1: * {h}
        #AT@language python

        class AtOthersTestClass:
            #AT+others
            #AT+node:ekr.20211103092443.1: ** method1
            def method1(self):
                pass
            #AT-others
        #AT-leo
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
    #@+node:ekr.20211101155930.1: *3* TestFast.test_clones
    def test_clones(self):

        c, x = self.c, self.x
        h = '@file /test/test_clones.py'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101155930.2: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        #AT+leo-ver=5-thin
        #AT+node:ekr.20211101152532.1: * {h}
        #AT@language python

        a = 1

        #AT+others
        #AT+node:ekr.20211101152631.1: ** cloned node
        a = 2
        #AT+node:ekr.20211101153300.1: *3* child
        a = 3
        #AT+node:ekr.20211101152631.1: ** cloned node
        a = 2
        #AT+node:ekr.20211101153300.1: *3* child
        a = 3
        #AT-others
        #AT-leo
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
        child1 = root.firstChild()
        child2 = child1.next()
        grand_child1 = child1.firstChild()
        grand_child2 = child2.firstChild()
        table = (
            (child1, 'cloned node'),
            (child2, 'cloned node'),
            (grand_child1, 'child'),
            (grand_child2, 'child'),
        )
        for child, h in table:
            self.assertEqual(child.h, h)
        self.assertTrue(child1.isCloned())
        self.assertTrue(child2.isCloned())
        self.assertEqual(child1.v, child2.v)
        self.assertFalse(grand_child1.isCloned())
        self.assertFalse(grand_child2.isCloned())
    #@+node:ekr.20211103080718.1: *3* TestFast.test_cweb
    #@@language python

    def test_cweb(self):

        c, x = self.c, self.x
        h = '@file /test/test_cweb.w'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211103080718.2: *4* << define contents >>
        # pylint: disable=anomalous-backslash-in-string
        contents = textwrap.dedent(f'''\
            ATq@@+leo-ver=5-thin@>
            ATq@@+node:ekr.20211103080829.1: * @{h}@>
            ATq@@@@language cweb@>
            ATq@@@@comment @@q@@ @@>@>
            
            % This is limbo in cweb mode... It should be in BSLaTeX mode, not BSc mode.
            % The following should not be colorized: class,if,else.
            
            @* this is a _cweb_ comment.  Code is written in BSc.
            "strings" should not be colorized.
            It should be colored in BSLaTeX mode.
            The following are not keywords in latex mode: if, else, etc.
            Section references are _valid_ in cweb comments!
            ATq@@+LB section ref 1 >>@>
            ATq@@+node:ekr.20211103082104.1: ** LB section ref 1 >>@>
            This is section 1.
            ATq@@-LB section ref 1 >>@>
            @c
            
            and this is C code. // It is colored in BSLaTeX mode by default.
            /* This is a C block comment.  It may also be colored in restricted BSLaTeX mode. */
            
            // Section refs are valid in code too, of course.
            ATq@@+LB section ref 2 >>@>
            ATq@@+node:ekr.20211103083538.1: ** LB section ref 2 >>@>
            This is section 2.
            ATq@@-LB section ref 2 >>@>
            
            BSLaTeX and BSc should not be colored.
            if else, while, do // C keywords.
            ATq@@-leo@>
        ''').replace('AT', '@').replace('LB', '<<').replace('BS', '\\')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
    #@+node:ekr.20211101152817.1: *3* TestFast.test_doc_parts
    def test_doc_parts(self):

        c, x = self.c, self.x
        h = '@file /test/test_directives.py'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101152843.1: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        #AT+leo-ver=5-thin
        #AT+node:ekr.20211101152532.1: * {h}
        #AT@language python

        a = 1

        #AT+at A doc part
        # Line 2.
        #AT@c

        #AT+doc
        # Line 2
        #
        # Line 3
        #AT@c

        #AT-leo
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
    #@+node:ekr.20211101154632.1: *3* TestFast.test_html_doc_part
    def test_html_doc_part(self):

        c, x = self.c, self.x
        h = '@file /test/test_html_doc_part.py'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101154651.1: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        <!--AT+leo-ver=5-thin-->
        <!--AT+node:ekr.20211101154334.1: * {h}-->
        <!--AT@language html-->

        <!--AT+at-->
        <!--
        Line 1.

        Line 2.
        -->
        <!--AT@c-->
        <!--AT-leo-->
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
    #@+node:ekr.20211101180354.1: *3* TestFast.test_verbatim
    def test_verbatim(self):

        c, x = self.c, self.x
        h = '@file /test/test_verbatim.py'
        root = c.rootPosition()
        root.h = h # To match contents.
        #@+<< define contents >>
        #@+node:ekr.20211101180404.1: *4* << define contents >>
        # Be careful: no line should look like a Leo sentinel!
        contents = textwrap.dedent(f'''\
        #AT+leo-ver=5-thin
        #AT+node:ekr.20211101175710.1: * {h}
        #AT@language python

        #AT+LB test >>
        #AT+node:ekr.20211101175745.1: ** LB test >>
        print('hi')
        #AT-LB test >>
        #ATafterref
         #AT+LB after

        #ATverbatim
        #AT+node (should be protected by verbatim)

        #AT-leo
        ''').replace('AT', '@').replace('LB', '<<')
        #@-<< define contents >>
        x.read_into_root(contents, path='test', root=root)
        s = c.atFileCommands.atFileToString(root, sentinels=True)
        self.assertEqual(contents, s)
    #@-others
#@-others
#@-leo
