#@+leo-ver=5-thin
#@+node:ekr.20211209153303.1: * @file ../plugins/importers/python.py
"""The new, tokenize based, @auto importer for Python."""
from __future__ import annotations
import os
import re
from typing import Optional, TYPE_CHECKING
import leo.core.leoGlobals as g
from leo.plugins.importers.base_importer import Block, Importer

if TYPE_CHECKING:
    assert g
    from leo.core.leoCommands import Commands as Cmdr
    from leo.core.leoNodes import Position

#@+others
#@+node:ekr.20220720043557.1: ** class Python_Importer
class Python_Importer(Importer):
    """Leo's Python importer"""

    language = 'python'
    string_list = ['"""', "'''", '"', "'"]  # longest first.
    allow_preamble = True

    # The default patterns. Overridden in the Cython_Importer class.
    # Group 1 matches the name of the class/def.
    async_def_pat = re.compile(r'\s*async\s+def\s+(\w+)\s*\(')
    def_pat = re.compile(r'\s*def\s+(\w+)\s*\(')
    class_pat = re.compile(r'\s*class\s+(\w+)')

    block_patterns: tuple = (
        ('class', class_pat),
        ('async def', async_def_pat),
        ('def', def_pat),
    )

    #@+others
    #@+node:ekr.20230825100219.1: *3* python_i.adjust_headlines
    def adjust_headlines(self, parent: Position) -> None:
        """
        python_i.adjust_headlines.

        coffee_script_i also uses this method.

        Add class names for all methods.

        Change 'def' to 'function:' for all non-methods.
        """
        for child in parent.subtree():
            found = False
            if child.h.startswith('def '):
                # Look up the tree for the nearest class.
                for ancestor in child.parents():
                    if ancestor == parent:
                        break
                    m = self.class_pat.match(ancestor.h)
                    if m:
                        found = True
                        # Replace 'def ' by the class name + '.'
                        child.h = f"{m.group(1)}.{child.h[4:].strip()}"
                        break
                if not found:
                    # Replace 'def ' by 'function'
                    child.h = f"function: {child.h[4:].strip()}"
    #@+node:ekr.20230830113521.1: *3* python_i.adjust_at_others
    def adjust_at_others(self, parent: Position) -> None:
        """
        Add a blank line before @others, and remove the leading blank line in the first child.
        """
        for p in parent.subtree():
            if p.h.startswith('class') and p.hasChildren():
                child = p.firstChild()
                lines = g.splitLines(p.b)
                for i, line in enumerate(lines):
                    if line.strip().startswith('@others') and child.b.startswith('\n'):
                        p.b = ''.join(lines[:i]) + '\n' + ''.join(lines[i:])
                        child.b = child.b[1:]
                        break
    #@+node:ekr.20230830051934.1: *3* python_i.delete_comments_and_strings
    string_pat1 = re.compile(r'([fFrR]*)("""|")')
    string_pat2 = re.compile(r"([fFrR]*)('''|')")

    def delete_comments_and_strings(self, lines: list[str]) -> list[str]:
        """
        Python_i.delete_comments_and_strings.

        This method handles f-strings properly.
        """

        def skip_string(delim: str, i: int, line: str) -> tuple[str, int]:
            """
            Skip the remainder of a string.

            String ends:      return ('', i)
            String continues: return (delim, len(line))
            """
            if delim not in line:
                return delim, len(line)
            delim_pat = re.compile(delim)
            while i < len(line):
                ch = line[i]
                if ch == '\\':
                    i += 2
                    continue
                if delim_pat.match(line, i):
                    return '', i + len(delim)
                i += 1
            return delim, i

        delim: str = ''  # The open string delim.
        result: list[str] = []
        for line_i, line in enumerate(lines):
            i, result_line = 0, []
            while i < len(line):
                if delim:
                    delim, i = skip_string(delim, i, line)
                    continue
                ch = line[i]
                if ch in '#\n':
                    break
                m = (
                    self.string_pat1.match(line, i) or
                    self.string_pat2.match(line, i)
                )
                if m:
                    # Start skipping the string.
                    prefix, delim = m.group(1), m.group(2)
                    i += len(prefix)
                    i += len(delim)
                    if i < len(line):
                        delim, i = skip_string(delim, i, line)
                else:
                    result_line.append(ch)
                    i += 1

            # End the line and append it to the result.
            if line.endswith('\n'):
                result_line.append('\n')
            result.append(''.join(result_line))
        assert len(result) == len(lines)  # A crucial invariant.
        return result
    #@+node:ekr.20230612171619.1: *3* python_i.create_sections
    def create_sections(self, parent: Position, result_blocks: list[Block]) -> None:
        """
        Python_Importer.create_sections:

        Create section reference nodes for docstrings and preamble code.

        Insert corresponding section references into parent.b.
        """
        ### g.trace('id(parent)', id(parent), 'id(parent.v)', id(parent.v), parent.h)

        assert self.allow_preamble
        assert parent == self.root
        lines = self.lines
        common_lws = self.compute_common_lws(result_blocks)
        preamble_start = max(0, result_blocks[1].start_body - 1)
        preamble_lines = lines[:preamble_start]

        if not preamble_lines or not any(z for z in preamble_lines):
            return

        #@+others  # Define helpers
        #@+node:ekr.20230922023223.1: *4* function: make_section_reference
        def make_section_reference(headline: str) -> Position:
            """
            Create a new section definition node and prepend a reference to parent.b.

            Return the newly-created node.
            """
            # Compute the section name.
            parent_s = os.path.split(parent.h)[1].replace('@file', '').replace('@clean', '').strip()
            section_name = f"<< {parent_s}: {headline} >>"

            # Create the child node.
            child = parent.insertAsFirstChild()
            child.h = section_name

            # Prepend the section reference in parent.b.
            parent.b = f"{common_lws}{section_name}\n" + parent.b
            return child
        #@+node:ekr.20230922023225.1: *4* function: find_docstring
        def find_docstring() -> list[str]:
            """Return the list of lines of a docstring, if any."""
            i = 0
            while i < len(preamble_lines):
                for delim in ('"""', "'''"):
                    if preamble_lines[i].count(delim) == 1:
                        i += 1
                        while i < len(preamble_lines):
                            if preamble_lines[i].count(delim) == 1:
                                return preamble_lines[: i + 1]
                            i += 1
                        return []  # Mal-formed docstring.
                i += 1
            return []
        #@-others


        v1 = result_blocks[1].v
        lines = g.splitLines(v1.b)

        # Special case: one-line docstring.
        line0 = preamble_lines[0].strip()  ###lines[0].strip()
        if False:  ###line0.startswith('"""') and line0.endswith('"""'):
            # Adjust the preamble lines and leave the first line alone."
            preamble_lines = preamble_lines[1:]
            v1.b = line0 + self.compute_body(lines[len(preamble_lines) :])
        else:
            # Remove the preamble lines from result_blocks[1], the first child block.
            v1.b = self.compute_body(lines[len(preamble_lines) :])

        # Prepend section references to parent.b and create the corresponding section reference nodes.
        docstring_lines = find_docstring()
        if docstring_lines:
            declaration_lines = preamble_lines[len(docstring_lines) :]
            # Prepend the lines in reverse order.
            if declaration_lines:
                declarations_p = make_section_reference("declarations")
                declarations_p.b = self.compute_body(declaration_lines)
            docstring_p = make_section_reference("docstring")
            docstring_p.b = self.compute_body(docstring_lines)
        else:
            preamble_p = make_section_reference("preamble")
            preamble_p.b = self.compute_body(preamble_lines)

        if 0:  ###
            print('create_sections: final results')
            for z in parent.self_and_subtree():
                g.printObj(g.splitLines(z.b), tag=f"{g.my_name()} {z.h}")
    #@+node:ekr.20230514140918.1: *3* python_i.find_blocks
    def find_blocks(self, i1: int, i2: int) -> list[Block]:
        """
        Python_Importer.find_blocks: override Importer.find_blocks.

        Using self.block_patterns and self.guide_lines, return a list of all
        blocks in the given range of *guide* lines.

        **Important**: An @others directive will refer to the returned blocks,
                       so there must be *no gaps* between blocks!
        """
        i, prev_i, results = i1, i1, []

        def lws_n(s: str) -> int:
            """Return the length of the leading whitespace for s."""
            return len(s) - len(s.lstrip())

        # Look behind to see what the previous block was.
        prev_block_line = self.guide_lines[i1 - 1] if i1 > 0 else ''
        while i < i2:
            progress = i
            s = self.guide_lines[i]
            i += 1
            for kind, pattern in self.block_patterns:
                m = pattern.match(s)
                if m:
                    # cython may include trailing whitespace.
                    name = m.group(1).strip()
                    end = self.find_end_of_block(i, i2)
                    assert i1 + 1 <= end <= i2, (i1, end, i2)

                    # #3517: Don't generate nested defs.
                    if (kind == 'def'
                        and prev_block_line.strip().startswith('def ')
                        and lws_n(prev_block_line) < lws_n(s)
                    ):
                        i = end
                    else:
                        block = Block(kind, name, start=prev_i, start_body=i, end=end, lines=self.lines)
                        results.append(block)
                        i = prev_i = end
                    break
            assert i > progress, g.callers()
        return results
    #@+node:ekr.20230514140918.4: *3* python_i.find_end_of_block
    def find_end_of_block(self, i: int, i2: int) -> int:
        """
        i is the index of the class/def line (within the *guide* lines).

        Return the index of the line *following* the entire class/def

        Note: All following blank/comment lines are *excluded* from the block.
        """
        def lws_n(s: str) -> int:
            """Return the length of the leading whitespace for s."""
            return len(s) - len(s.lstrip())

        if i >= i2:
            return i2

        prev_line = self.guide_lines[i - 1]
        kinds = ('class', 'def', '->')  # '->' denotes a coffeescript function.
        assert any(z in prev_line for z in kinds), (i, repr(prev_line))

        # Handle multi-line def's. Scan to the line containing a close parenthesis.
        if prev_line.strip().startswith('def ') and ')' not in prev_line:
            while i < i2:
                i += 1
                if ')' in self.guide_lines[i - 1]:
                    break
        tail_lines = 0
        if i < i2:
            lws1 = lws_n(prev_line)
            while i < i2:
                s = self.guide_lines[i]
                i += 1
                if s.strip():
                    if lws_n(s) <= lws1:
                        # A non-comment line that ends the block.
                        # Exclude all tail lines.
                        return i - tail_lines - 1
                    # A non-comment line that does not end the block.
                    tail_lines = 0
                else:
                    # A comment line.
                    tail_lines += 1
        return i2 - tail_lines
    #@+node:ekr.20230825111112.1: *3* python_i.move_docstrings
    def move_docstrings(self, parent: Position) -> None:
        """
        Move docstrings to their most convenient locations.
        """

        delims = ('"""', "'''")

        #@+others  # define helper functions
        #@+node:ekr.20230825164231.1: *4* function: find_docstrings
        def find_docstring(p: Position) -> Optional[str]:
            """Righting a regex that will return a docstring is too tricky."""
            s_strip = p.b.strip()
            if not s_strip:
                return None
            if not s_strip.startswith(delims):
                return None
            delim = delims[0] if s_strip.startswith(delims[0]) else delims[1]
            lines = g.splitLines(p.b)
            if lines[0].count(delim) == 2:
                return lines[0]
            i = 1
            while i < len(lines):
                if delim in lines[i]:
                    return ''.join(lines[: i + 1])
                i += 1
            return None

        #@+node:ekr.20230825164234.1: *4* function: move_docstring
        def move_docstring(parent: Position) -> None:
            """Move a docstring from the child (or next sibling) to the parent."""
            child = parent.firstChild() or parent.next()
            if not child:
                return
            docstring = find_docstring(child)
            if not docstring:
                return
            child.b = child.b[len(docstring) :]
            if parent.h.startswith('class'):
                parent_lines = g.splitLines(parent.b)
                # Count the number of parent lines before the class line.
                n = 0
                while n < len(parent_lines):
                    line = parent_lines[n]
                    n += 1
                    if line.strip().startswith('class '):
                        break
                if n > len(parent_lines):
                    g.printObj(g.splitLines(parent.b), tag=f"Noclass line: {p.h}")
                    return
                # This isn't perfect in some situations.
                docstring_list = [f"{' '*4}{z}" for z in g.splitLines(docstring)]
                parent.b = ''.join(parent_lines[:n] + docstring_list + parent_lines[n:])
            else:
                if 0:  ###  WRONG for top-level node!
                    parent.b = docstring + parent.b

            # Delete references to empty children.
            # ric.remove_empty_nodes will delete the child later.
            if not child.b.strip():
                parent.b = parent.b.replace(child.h, '')
        #@-others

        # python_i.gen_block has already generated the top-level docstring.

        # Move class docstrings.
        for p in parent.subtree():
            if p.h.startswith('class '):
                move_docstring(p)
    #@+node:ekr.20230825095926.1: *3* python_i.postprocess
    def postprocess(self, parent: Position) -> None:
        """Python_Importer.postprocess."""
        # See #3514.
        self.adjust_headlines(parent)
        self.move_docstrings(parent)
        self.adjust_at_others(parent)
    #@-others
#@-others

def do_import(c: Cmdr, parent: Position, s: str) -> None:
    """The importer callback for python."""
    Python_Importer(c).import_from_string(parent, s)

importer_dict = {
    'extensions': ['.py', '.pyw', '.pyi', '.codon'],  # mypy uses .pyi extension.
    'func': do_import,
}
#@@language python
#@@tabwidth -4
#@-leo
