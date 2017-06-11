from __future__ import (absolute_import, division, print_function)

import logging
import neovim
from . import check_lldb

__metaclass__ = type  # pylint: disable=invalid-name

if not check_lldb.probe():
    logging.getLogger(__name__).critical('LLDB could not be imported!')
    # ImportError will be raised in Controller import below.

# pylint: disable=wrong-import-position
from .controller import Controller, EventLoopError  # NOQA
from .vim_x import VimX  # NOQA
# pylint: enable=wrong-import-position


@neovim.plugin  # pylint: disable=too-few-public-methods
class Middleman:

    def __init__(self, vim):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.ctrl = Controller(VimX(vim))
        self.ctrl.start()
        if self.ctrl.vimx._vim_test:  # pylint: disable=protected-access
            print("Note: `:LL-` commands are not bound with this test instance")
        else:
            vim.command('call lldb#remote#init(%d)' % vim.channel_id)

    # The only interface that is predefined in the remote plugin manifest file.
    # The first execution of `:LLsession` initializes the remote part of the plugin.
    @neovim.command('LLsession', nargs='+', complete='customlist,lldb#session#complete')
    def _session(self, args):
        self.ctrl.safe_call(self.ctrl.session.handle, args)

    @neovim.rpc_export('mode')
    def _mode(self, mode):
        self.ctrl.safe_call(self.ctrl.session.mode_setup, [mode])

    @neovim.rpc_export('exec')
    def _exec(self, *args):
        if len(args) == 0:
            self.ctrl.vimx.log("Usage :LL <lldb-command> [args...]", level=2)
        elif args[0] in ['di', 'dis', 'disassemble']:
            self.ctrl.safe_call(self.ctrl.change_buffer_cmd, ['disassembly', ' '.join(args)])
        elif args[0] in ['bt', '_regexp-bt']:
            self.ctrl.safe_call(self.ctrl.change_buffer_cmd, ['backtrace', ' '.join(args)])
        else:
            self.ctrl.safe_execute(args)
            if args[0] == 'help':
                self.ctrl.vimx.command('drop [lldb]logs')

    @neovim.rpc_export('stdin')
    def _stdin(self, strin):
        self.ctrl.safe_call(self.ctrl.put_stdin, [strin])

    @neovim.rpc_export('exit')
    def _exit(self):
        self.ctrl.safe_exit()

    @neovim.rpc_export('complete', sync=True)
    def _complete(self, arg, line, pos):
        # FIXME user-customizable timeout?
        try:
            return self.ctrl.safe_call(self.ctrl.complete_command,
                                       [arg, line, pos], True, timeout=3)
        except EventLoopError as e:
            self.logger.warn("%s on %s | %s", str(e), repr(line[:pos]), repr(line[pos:]))
            return []

    @neovim.rpc_export('get_modes', sync=True)
    def _get_modes(self):
        try:
            return self.ctrl.safe_call(self.ctrl.session.get_modes,
                                       [], True, timeout=1)
        except EventLoopError as e:
            self.logger.warn(str(e))
            return []

    @neovim.rpc_export('select_thread_and_frame')
    def _select_thread_and_frame(self, thread_and_frame_idx):
        if thread_and_frame_idx[0]:
            self.ctrl.safe_execute(['thread', 'select', thread_and_frame_idx[0]])
        if thread_and_frame_idx[1]:
            self.ctrl.safe_execute(['frame', 'select', thread_and_frame_idx[1]])

    @neovim.rpc_export('btswitch')
    def _btswitch(self):
        self.ctrl.safe_call(self.ctrl.do_btswitch)

    @neovim.rpc_export('breakswitch')
    def _breakswitch(self, bufnr, line):
        self.ctrl.safe_call(self.ctrl.do_breakswitch, [bufnr, line])

    @neovim.rpc_export('breakdelete')
    def _breakdelete(self, bp_id):
        self.ctrl.safe_call(self.ctrl.do_breakdelete, [bp_id])

    @neovim.rpc_export('refresh')
    def _refresh(self):
        self.ctrl.safe_call(self.ctrl.update_buffers)

    @neovim.rpc_export('watchswitch')
    def _watchpoint(self, var_name):
        pass  # TODO create watchpoint from locals pane
