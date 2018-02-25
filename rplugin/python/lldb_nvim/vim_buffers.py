# Manages Vim user interface.
#
# TODO: display watched expressions
# TODO: define interface for interactive panes, like catching enter
#        presses to change selected frame/thread...

from __future__ import (absolute_import, division, print_function)

from os.path import exists as path_exists
from . import lldb_utils as llu
from .vim_signs import BPSign, PCSign

__metaclass__ = type  # pylint: disable=invalid-name


class VimBuffers:  # pylint: disable=too-many-instance-attributes
    content_map = {
        "backtrace": "bt",
        "breakpoints": "breakpoint list",
        "disassembly": "disassemble -c 20 -p",
        "threads": "thread list",
        "locals": "frame variable",
        "registers": "register read"
    }

    def __init__(self, ctrl, vimx):
        """ Declare VimBuffers state variables """
        import logging
        self.ctrl = ctrl
        self.vimx = vimx
        self.logger = logging.getLogger(__name__)

        self.buf_map = {}

        # Currently shown signs
        self.bp_signs = {}  # maps (bufnr, line) -> <BPSign object>
        self.bp_list = {}  # maps (bufnr, line) -> [<SBBreakpoint object>, ...]
        self.pc_signs = {}
        self.pc_cur_loc = None

    def buf_map_check(self):
        if not self.buf_map:
            self.buf_map = self.vimx.init_buffers()

    def update_pc(self, target):  # pylint: disable=too-many-branches
        """ Place the PC sign on the PC location of each thread's selected frame.
            If the 'selected' PC location has changed, jump to it.
        """

        # Clear all existing PC signs
        for sign in self.pc_signs.values():
            sign.hide()
        self.pc_signs = {}

        if target is None or not target.IsValid():
            return
        process = target.GetProcess()
        if process is None or not process.IsValid() or not process.is_alive:
            return

        # Show a PC marker for each thread
        for thread in process:
            loc = llu.get_pc_source_loc(thread, self.ctrl.get_command_result)
            if not loc:
                # no valid source locations for PCs. hide all existing PC markers
                continue

            (_, fname, line) = loc
            self.logger.info("Got pc loc: %s", repr(loc))
            is_selected = thread.GetIndexID() == process.GetSelectedThread().GetIndexID()
            if path_exists(fname):
                bufnr = self.vimx.buffer_add(fname)
            else:
                continue

            hidden = not is_selected and (bufnr, line) in self.pc_signs
            sign = PCSign(self.vimx, bufnr, line, is_selected, hidden)
            self.pc_signs[(bufnr, line)] = sign

            if is_selected and self.pc_cur_loc != (bufnr, line):
                self.vimx.sign_jump(bufnr, sign.id)
                self.pc_cur_loc = (bufnr, line)

    def logs_append(self, outstr, prefix=None):
        """ Returns the number lines appended """
        self.buf_map_check()

        if len(outstr) == 0:
            return 0
        lines = outstr.replace('\r\n', '\n').split('\n')
        if prefix is not None:
            last_line = lines[-1]
            if len(last_line) > 0:
                last_line = prefix + last_line
            lines = [prefix + line for line in lines[:-1]] + [last_line]
        self.vimx.update_noma_buffer(self.buf_map['logs'], lines, append=True)
        self.vimx.buffer_scroll_bottom(self.buf_map['logs'])
        return len(lines) - 1

    def update_breakpoints(self, target, hard_update=False):  # pylint: disable=too-many-branches
        """ Decorates buffer with signs corresponding to breakpoints in target. """

        self.bp_list = {}
        if target is None or not target.IsValid():
            for (key, sign) in self.bp_signs.items():
                if not sign.hidden:
                    sign.hide()
            return

        needed_bps = set()
        source_map = llu.settings_target_source_map(self.ctrl.get_command_result)
        for bp in target.breakpoint_iter():
            bplocs = llu.get_bploc_tuples(bp, source_map)
            for (filepath, line) in bplocs:
                if filepath and path_exists(filepath):
                    bufnr = self.vimx.buffer_add(filepath)
                    key = (bufnr, line)
                    needed_bps.add(key)
                    if key in self.bp_list:
                        self.bp_list[key].append(bp)
                    else:
                        self.bp_list[key] = [bp]

        # Hide all (outdated) breakpoint signs
        new_bps = needed_bps
        bp_signs = self.bp_signs.copy()
        for (key, sign) in bp_signs.items():
            if hard_update or key not in new_bps:
                sign.hide()
                del self.bp_signs[key]
            else:
                if bp_signs[key].hidden:
                    bp_signs[key].show()
                new_bps.discard(key)

        # Show all (new) breakpoint signs
        for (bufnr, line) in new_bps:
            self.bp_signs[(bufnr, line)] = BPSign(
                self.vimx, bufnr, line, (bufnr, line) in self.pc_signs)

    def update_buffer(self, buf, target):
        self.buf_map_check()

        command = self.content_map[buf]
        proc_stat = llu.get_process_stat(target)[1]
        success, output = self.ctrl.get_command_result(command)
        if not success and proc_stat:
            output = proc_stat
        if output is None:
            output = ''
        results = output.split('\n')

        if buf == 'breakpoints':
            self.update_breakpoints(target)

        self.vimx.update_noma_buffer(self.buf_map[buf], results)

    def update(self, target):
        """ Updates signs, buffers, and possibly jumps to pc. """
        self.update_pc(target)

        for buf in self.content_map:
            self.update_buffer(buf, target)
