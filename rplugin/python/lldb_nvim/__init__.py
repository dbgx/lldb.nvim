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
  def _start(self, args):
    self.ctrl.safe_call(self.ctrl.session.handle, args)

  @neovim.rpc_export('exit')
  def _exit(self):
    self.ctrl.safe_exit()

  @neovim.rpc_export('complete', sync=True)
  def _complete(self, arg, line, pos):
    assert line[:2] == 'LL'
    line = line[2:]
    pos = int(pos) - 2

    if line.startswith('regexp'):
      line = '_regexp-' + line.lstrip('regexp')
      pos += 2

    return self.ctrl.safe_call(self.ctrl.complete_command,
                               [arg, line, pos], True)

  @neovim.rpc_export('apropos')
  def _apropos(self, keyword):
    self.ctrl.safe_execute("apropos", keyword)

  @neovim.rpc_export('breakpoint')
  def _breakpoint(self, *args):
    self.ctrl.safe_call(self.ctrl.do_breakpoint, [' '.join(args)])

  @neovim.rpc_export('breakswitch')
  def _breakswitch(self, bufnr, line):
    self.ctrl.safe_call(self.ctrl.do_breakswitch, [bufnr, line])

  @neovim.rpc_export('bt')
  def _bt(self):
    self.ctrl.vimx.command('drop backtrace')

  @neovim.rpc_export('command')
  def _command(self, *args):
    self.ctrl.safe_execute("command", args)

  @neovim.rpc_export('continue')
  def _continue(self, *args):
    self.ctrl.safe_execute("continue", args)

  @neovim.rpc_export('detach')
  def _detach(self, *args):
    self.ctrl.safe_execute("detach", args)

  @neovim.rpc_export('disassemble')
  def _disassemble(self, *args):
    self.ctrl.safe_call(self.ctrl.do_disassemble, [' '.join(args)])
    self.ctrl.vimx.command('drop disassembly')

  @neovim.rpc_export('down')
  def _down(self, *args):
    n = "1" if len(args) == 0 else args[0]
    self.ctrl.safe_call(self.ctrl.do_frame, ['select -r -' + n])

  @neovim.rpc_export('expression')
  def _expression(self, *args):
    self.ctrl.safe_execute("expression", args)

  @neovim.rpc_export('frame')
  def _frame(self, *args):
    self.ctrl.safe_call(self.ctrl.do_frame, [' '.join(args)])

  @neovim.rpc_export('help')
  def _help(self, *args):
    self.ctrl.safe_execute("help", args)

  @neovim.rpc_export('log')
  def _log(self, *args):
    self.ctrl.safe_execute("log", args)

  @neovim.rpc_export('platform')
  def _platform(self, *args):
    self.ctrl.safe_execute("platform", args)

  @neovim.rpc_export('plugin')
  def _plugin(self, *args):
    self.ctrl.safe_execute("plugin", args)

  @neovim.rpc_export('po')
  def _po(self, *args):
    self.ctrl.safe_execute("po", args)

  @neovim.rpc_export('print')
  def _print(self, *args):
    self.ctrl.safe_execute("print", args)

  @neovim.rpc_export('process')
  def _process(self, *args):
    self.ctrl.safe_call(self.ctrl.do_process, [' '.join(args)])

  @neovim.rpc_export('refresh')
  def _refresh(self):
    self.ctrl.safe_call(self.ctrl.update_buffers, [False, '!all'])

  @neovim.rpc_export('regexpbreak')
  def _regexpbreak(self, *args):
    # FIXME update buffers
    self.ctrl.safe_execute("_regexp-break", args)

  @neovim.rpc_export('register')
  def _register(self, *args):
    self.ctrl.safe_execute("register", args)

  @neovim.rpc_export('settings')
  def _settings(self, *args):
    self.ctrl.safe_execute("settings",args)

  @neovim.rpc_export('source')
  def _source(self, *args):
    self.ctrl.safe_execute("source", args)

  @neovim.rpc_export('target')
  def _target(self, *args):
    self.ctrl.safe_call(self.ctrl.do_target, [' '.join(args)])

  @neovim.rpc_export('tbreak')
  def _tbreak(self, *args):
    # FIXME update buffers
    self.ctrl.safe_execute("tbreak", args)

  @neovim.rpc_export('thread')
  def _thread(self, *args):
    self.ctrl.safe_call(self.ctrl.do_thread, [' '.join(args)])

  @neovim.rpc_export('type')
  def _type(self, *args):
    self.ctrl.safe_execute("type", args)

  @neovim.rpc_export('up')
  def _up(self, *args):
    n = "1" if len(args) == 0 else args[0]
    self.ctrl.safe_call(self.ctrl.do_frame, ['select -r +' + n])

  @neovim.rpc_export('version')
  def _version(self):
    self.ctrl.safe_execute("version", [])

  @neovim.rpc_export('watchpoint')
  def _watchpoint(self, *args):
    self.ctrl.safe_execute("watchpoint", args)

  @neovim.rpc_export('finish')
  def _finish(self, *args):
    self.ctrl.safe_execute("finish", args)

  @neovim.rpc_export('next')
  def _next(self, *args):
    self.ctrl.safe_execute("next", args)

  @neovim.rpc_export('step')
  def _step(self, *args):
    self.ctrl.safe_execute("step", args)
