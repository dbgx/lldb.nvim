import neovim
import check_lldb

lldb_success = check_lldb.probe()

from .controller import Controller
from .vim_x import VimX

@neovim.plugin
class Middleman(object):
  def __init__(self, vim):
    import logging
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)
    if not lldb_success:
      self.logger.critical('LLDB could not be imported!')
      # ImportError will be raised in Controller init below.
    self.ctrl = Controller(VimX(vim))
    self.ctrl.start()
    vim.command('call lldb#remote#init(%d)' % vim.channel_id)

  @neovim.command('LLsession', nargs='+', complete='customlist,lldb#session#complete')
  def _session(self, args):
    self.ctrl.safe_call(self.ctrl.session.handle, args)

  @neovim.rpc_export('mode')
  def _mode(self, mode):
    self.ctrl.safe_call(self.ctrl.session.mode_setup, [mode])

  @neovim.rpc_export('exec')
  def _exec(self, *args):
    if args[0] == 'disassemble':
      self.ctrl.safe_call(self.ctrl.do_disassemble, [' '.join(args)])
      if self.ctrl._target is not None:
        self.ctrl.vimx.command('drop [lldb]disassembly')
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
    except Exception:
      return []

  @neovim.rpc_export('get_modes', sync=True)
  def _get_modes(self):
    try:
      return self.ctrl.safe_call(self.ctrl.session.get_modes,
                                 [], True, timeout=1)
    except Exception:
      return []

  @neovim.rpc_export('breakswitch')
  def _breakswitch(self, bufnr, line):
    self.ctrl.safe_call(self.ctrl.do_breakswitch, [bufnr, line])

  @neovim.rpc_export('refresh')
  def _refresh(self):
    self.ctrl.safe_call(self.ctrl.update_buffers, [False])

  @neovim.rpc_export('watchswitch')
  def _watchpoint(self, var_name):
    pass # TODO create watchpoint from locals pane
