# Classes responsible for placing signs in the Vim user interface.

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type  # pylint: disable=invalid-name


class VimSign:
    SIGN_BREAKPOINT = "llsign_bpres"
    SIGN_PC_SELECTED = "llsign_pcsel"
    SIGN_PC_UNSELECTED = "llsign_pcunsel"

    # hopefully unique sign id (for `:sign place`)
    sign_id = 257

    # pylint: disable=too-many-arguments
    def __init__(self, vimx, name, bufnr, line, hidden):
        self.vimx = vimx
        self.id = VimSign.sign_id
        VimSign.sign_id += 1
        self.name = name
        self.bufnr = bufnr
        self.line = line
        if hidden:
            self.hidden = True
        else:
            self.show()
    # pylint: enable=too-many-arguments

    def show(self):
        self.vimx.sign_place(self.id, self.name, self.bufnr, self.line)
        self.hidden = False

    def hide(self):
        self.vimx.sign_unplace(self.id)
        self.hidden = True


class BPSign(VimSign):

    def __init__(self, vimx, bufnr, line, hidden=False):
        name = VimSign.SIGN_BREAKPOINT
        super(BPSign, self).__init__(vimx, name, bufnr, line, hidden)


class PCSign(VimSign):
    # pylint: disable=too-many-arguments

    def __init__(self, vimx, bufnr, line, selected, hidden=False):
        self.selected = selected
        name = VimSign.SIGN_PC_SELECTED if selected else VimSign.SIGN_PC_UNSELECTED
        super(PCSign, self).__init__(vimx, name, bufnr, line, hidden)
    # pylint: enable=too-many-arguments
