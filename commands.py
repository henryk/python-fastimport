# Copyright (C) 2008 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Import command classes."""


# Lists of command names
COMMAND_NAMES = ['blob', 'checkpoint', 'commit', 'progress', 'reset', 'tag']
FILE_COMMAND_NAMES = ['filemodify', 'filedelete', 'filecopy', 'filerename',
    'filedeleteall']

# Bazaar file kinds
FILE_KIND = 'file'
SYMLINK_KIND = 'symlink'


class ImportCommand(object):
    """Base class for import commands."""

    def __init__(self, name):
        self.name = name
        # List of field names not to display
        self._binary = []

    def dump_str(self, names=None, child_lists=None, verbose=False):
        """Dump fields as a string.

        :param names: the list of fields to include or
            None for all public fields
        :param child_lists: dictionary of child command names to
            fields for that child command to include
        :param verbose: if True, prefix each line with the command class and
            display fields as a dictionary; if False, dump just the field
            values with tabs between them
        """
        interesting = {}
        if names is None:
            fields = [k for k in self.__dict__.keys() if not k.startswith('_')]
        else:
            fields = names
        for field in fields:
            value = self.__dict__.get(field)
            if field in self._binary and value is not None:
                value = '(...)'
            interesting[field] = value
        if verbose:
            return "%s: %s" % (self.__class__.__name__, interesting)
        else:
            return "\t".join([repr(interesting[k]) for k in fields])


class BlobCommand(ImportCommand):

    def __init__(self, mark, data, lineno=0):
        ImportCommand.__init__(self, 'blob')
        self.mark = mark
        self.data = data
        self.lineno = lineno
        # Provide a unique id in case the mark is missing
        if mark is None:
            self.id = '@%d' % lineno
        else:
            self.id = ':' + mark
        self._binary = ['data']

    def __repr__(self):
        if self.mark is None:
            mark_line = ""
        else:
            mark_line = "\nmark :%s" % self.mark
        return "blob%s\ndata %d\n%s" % (mark_line, len(self.data), self.data)


class CheckpointCommand(ImportCommand):

    def __init__(self):
        ImportCommand.__init__(self, 'checkpoint')

    def __repr__(self):
        return "checkpoint"


class CommitCommand(ImportCommand):

    def __init__(self, ref, mark, author, committer, message, from_,
        merges, file_iter, lineno=0):
        ImportCommand.__init__(self, 'commit')
        self.ref = ref
        self.mark = mark
        self.author = author
        self.committer = committer
        self.message = message
        self.from_ = from_
        self.merges = merges
        self.file_iter = file_iter
        self.lineno = lineno
        self._binary = ['file_iter']
        # Provide a unique id in case the mark is missing
        if mark is None:
            self.id = '@%d' % lineno
        else:
            self.id = ':' + mark

    def __repr__(self):
        if self.mark is None:
            mark_line = ""
        else:
            mark_line = "\nmark :%s" % self.mark
        if self.author is None:
            author_line = ""
        else:
            author_line = "\nauthor %s" % _format_who_when(self.author)
        committer = "committer %s" % _format_who_when(self.committer)
        if self.message is None:
            msg = ""
        else:
            msg = "\ndata %d\n%s" % (len(self.message), self.message)
        if self.from_ is None:
            from_line = ""
        else:
            from_line = "\nfrom %s" % self.from_
        if self.merges is None:
            merge_lines = ""
        else:
            merge_lines = "".join(["\nmerge %s" % (m,)
                for m in self.merges])
        if self.file_iter is None:
            filecommands = ""
        else:
            filecommands = "".join(["\n%r" % (c,)
                for c in iter(self.file_iter)])
        return "commit %s%s%s\n%s%s%s%s%s" % (self.ref, mark_line, author_line,
            committer, msg, from_line, merge_lines, filecommands)

    def dump_str(self, names=None, child_lists=None, verbose=False):
        result = [ImportCommand.dump_str(self, names, verbose=verbose)]
        for f in self.file_iter():
            if child_lists is None:
                continue
            try:
                child_names = child_lists[f.name]
            except KeyError:
                continue
            result.append("\t%s" % f.dump_str(child_names, verbose=verbose))
        return '\n'.join(result)


class ProgressCommand(ImportCommand):

    def __init__(self, message):
        ImportCommand.__init__(self, 'progress')
        self.message = message

    def __repr__(self):
        return "progress %s" % (self.message,)


class ResetCommand(ImportCommand):

    def __init__(self, ref, from_):
        ImportCommand.__init__(self, 'reset')
        self.ref = ref
        self.from_ = from_

    def __repr__(self):
        if self.from_ is None:
            from_line = ""
        else:
            from_line = "\nfrom :%s" % self.from_
        return "reset %s%s" % (self.ref, from_line)


class TagCommand(ImportCommand):

    def __init__(self, id, from_, tagger, message):
        ImportCommand.__init__(self, 'tag')
        self.id = id
        self.from_ = from_
        self.tagger = tagger
        self.message = message

    def __repr__(self):
        if self.from_ is None:
            from_line = ""
        else:
            from_line = "\nfrom :%s" % self.from_
        if self.tagger is None:
            tagger_line = ""
        else:
            tagger_line = "\ntagger %s" % _format_who_when(self.tagger)
        if self.message is None:
            msg = ""
        else:
            msg = "\ndata %d\n%s" % (len(self.message), self.message)
        return "tag %s%s%s%s" % (self.id, from_line, tagger_line, msg)


class FileCommand(ImportCommand):
    """Base class for file commands."""
    pass


class FileModifyCommand(FileCommand):

    def __init__(self, path, kind, is_executable, dataref, data):
        # Either dataref or data should be null
        FileCommand.__init__(self, 'filemodify')
        self.path = path
        self.kind = kind
        self.is_executable = is_executable
        self.dataref = dataref
        self.data = data
        self._binary = ['data']

    def __repr__(self):
        if self.kind == 'symlink':
            mode = "120000"
        elif self.is_executable:
            mode = "755"
        else:
            mode = "644"
        if self.dataref is None:
            dataref = "inline"
            datastr = "\ndata %d\n%s" % (len(self.data), self.data)
        else:
            dataref = "%s" % (self.dataref,)
            datastr = ""
        return "M %s %s %s%s" % (mode, dataref, self.path, datastr)


class FileDeleteCommand(FileCommand):

    def __init__(self, path):
        FileCommand.__init__(self, 'filedelete')
        self.path = path

    def __repr__(self):
        return "D %s" % (self.path,)


class FileCopyCommand(FileCommand):

    def __init__(self, src_path, dest_path):
        FileCommand.__init__(self, 'filecopy')
        self.src_path = src_path
        self.dest_path = dest_path

    def __repr__(self):
        return "C %s %s" % (_quote_path(self.src_path), self.dest_path)


class FileRenameCommand(FileCommand):

    def __init__(self, old_path, new_path):
        FileCommand.__init__(self, 'filerename')
        self.old_path = old_path
        self.new_path = new_path

    def __repr__(self):
        return "R %s %s" % (_quote_path(self.old_path), self.new_path)


class FileDeleteAllCommand(FileCommand):

    def __init__(self):
        FileCommand.__init__(self, 'filedeleteall')

    def __repr__(self):
        return "deleteall"


def _quote_path(s):
    """Surround a path with quotes if it contains spaces."""
    if ' ' in s:
        return '"%s"' % (s,)
    else:
        return s


def _format_who_when(fields):
    """Format a tuple of name,email,secs-since-epoch,utc-offset-secs as a string."""
    offset = fields[3]
    if offset < 0:
        offset_sign = '-'
        offset = abs(offset)
    else:
        offset_sign = '+'
    offset_hours = offset / 3600
    offset_minutes = offset / 60 - offset_hours * 60
    offset_str = "%s%02d%02d" % (offset_sign, offset_hours, offset_minutes)
    return "%s <%s> %d %s" % (fields[0], fields[1], fields[2], offset_str)
