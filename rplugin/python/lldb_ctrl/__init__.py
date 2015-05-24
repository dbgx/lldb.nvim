import neovim
import check_lldb

from .controller import LLController

@neovim.plugin
class LLInterface(object):
  def __init__(self, vim):
    self.vim = vim
    if not check_lldb.probe():
      import sys
      vim.command('echom "Unable to load lldb module. Check lldb on the path is available (or LLDB is set)"')
      sys.exit(0)
    self.ctrl = LLController(self)
    vim.command('au VimLeavePre * call LLExit()')

  def log(self, msg, level=1):
    level_map = ['None', 'WarningMsg', 'ErrorMsg']
    msg = msg.replace('"', '\\"').replace('\n', '\\n')
    self.vim.command('echohl %s | echom "%s" | echohl None' % (level_map[level], msg,))

  def buffer_add(self, name):
    bufnr = self.vim.eval('bufnr("%s", 1)' % name)
    self.vim.command('call setbufvar(%d, "&bl", 1)' % bufnr)
    return bufnr

  def sign_place(self, sign_id, name, bufnr, line):
    cmd = "sign place %d name=%s line=%d buffer=%s" % (sign_id, name, line, bufnr)
    self.vim.command(cmd)

  def sign_unplace(self, id):
    self.vim.command("sign unplace %d" % id)

  def get_buffer_from_nr(self, nr):
    for b in self.vim.buffers:
      if b.number == nr:
        return b
    return None

  def get_buffers(self):
    return self.vim.buffers

  def buf_init(self):
    buf_map = self.vim.eval('LLBuffersInit()')
    return buf_map

  @neovim.function('LLBreakswitch')
  def _breakswitch(self, args):
    if len(args) != 2:
      self.log('LLBreakswitch takes exactly 2 arguments (%d given)', len(args))
      return
    path = self.get_buffer_from_nr(args[0]).name
    assert(path.startswith('/'))
    self.ctrl.do_breakswitch(path, args[1])

  @neovim.function('LLComplete', sync=True)
  def _complete(self, args):
    arg = args[0]
    line = args[1]
    pos = args[2]

    assert line[:2] == 'LL'
    # Remove first 'LL' characters that all commands start with
    line = line[2:]
    pos = int(pos) - 2

    results = self.ctrl.complete_command(arg, line, pos)
    return '%s\n' % '\n'.join(results)

  @neovim.function('LLExit', sync=True)
  def _exit(self):
    self.ctrl.do_exit()

  @neovim.command('LLrun', nargs='*')
  def _run(self, args):
    self.ctrl.do_process('launch ' + ' '.join(args))

  @neovim.command('LLstart', nargs='*')
  def _start(self, args):
    self.ctrl.do_process('launch -s ' + ' '.join(args))

  @neovim.command('LLattach', nargs='1')
  def _attach(self, args):
    self.ctrl.do_attach(' '.join(args))

  @neovim.command('LLdetach')
  def _detach(self):
    self.ctrl.do_detach()

  @neovim.command('LLapropos', nargs='*', complete='custom,LLComplete')
  def _apropos(self, args):
    self.ctrl.do_command("apropos", ' '.join(args))

  @neovim.command('LLbreakpoint', nargs='*', complete='custom,LLComplete')
  def _breakpoint(self, args):
    self.ctrl.do_breakpoint(' '.join(args))

  @neovim.command('LLbt', nargs='*', complete='custom,LLComplete')
  def _bt(self, args):
    self.ctrl.do_command("bt", ' '.join(args))

  @neovim.command('LLcommand', nargs='*', complete='custom,LLComplete')
  def _command(self, args):
    self.ctrl.do_command("command", ' '.join(args))

  @neovim.command('LLcontinue')
  def _continue(self):
    self.ctrl.do_continue()

  @neovim.command('LLdisassemble', nargs='*', complete='custom,LLComplete')
  def _disassemble(self, args):
    self.ctrl.do_command("disassemble", ' '.join(args))

  @neovim.command('LLexpression', nargs='*', complete='custom,LLComplete')
  def _expression(self, args):
    self.ctrl.do_command("expression", ' '.join(args))

  @neovim.command('LLframe', nargs='*', complete='custom,LLComplete')
  def _frame(self, args):
    self.ctrl.do_select("frame", ' '.join(args))

  @neovim.command('LLhelp', nargs='*', complete='custom,LLComplete')
  def _help(self, args):
    self.ctrl.do_command("help", ' '.join(args))

  @neovim.command('LLlog', nargs='*', complete='custom,LLComplete')
  def _log(self, args):
    self.ctrl.do_command("log", ' '.join(args))

  @neovim.command('LLplatform', nargs='*', complete='custom,LLComplete')
  def _platform(self, args):
    self.ctrl.do_command("platform",' '.join(args))

  @neovim.command('LLplugin', nargs='*', complete='custom,LLComplete')
  def _plugin(self, args):
    self.ctrl.do_command("plugin", ' '.join(args))

  @neovim.command('LLpo', nargs='*', complete='custom,LLComplete')
  def _po(self, args):
    self.ctrl.do_command("po", ' '.join(args))

  @neovim.command('LLprint', nargs='*', complete='custom,LLComplete')
  def _print(self, args):
    self.ctrl.do_command("print", ' '.join(args))

  @neovim.command('LLprocess', nargs='*', complete='custom,LLComplete')
  def _process(self, args):
    self.ctrl.do_process(' '.join(args))

  @neovim.command('LLrefresh')
  def _refresh(self): # FIXME see processPendingEvents()
    self.ctrl.processPendingEvents()

  @neovim.command('LLregexpattach', nargs='*', complete='custom,LLComplete')
  def _regexpattach(self, args):
    self.ctrl.do_command("_regexp-attach", ' '.join(args))

  @neovim.command('LLregexpbreak', nargs='*', complete='custom,LLComplete')
  def _regexpbreak(self, args):
    self.ctrl.do_command("_regexp-break", ' '.join(args))

  @neovim.command('LLregexpbt', nargs='*', complete='custom,LLComplete')
  def _regexpbt(self, args):
    self.ctrl.do_command("_regexp-bt", ' '.join(args))

  @neovim.command('LLregexpdown', nargs='*', complete='custom,LLComplete')
  def _regexpdown(self, args):
    self.ctrl.do_command("_regexp-down", ' '.join(args))

  @neovim.command('LLregexptbreak', nargs='*', complete='custom,LLComplete')
  def _regexptbreak(self, args):
    self.ctrl.do_command("_regexp-tbreak", ' '.join(args))

  @neovim.command('LLregexpdisplay', nargs='*', complete='custom,LLComplete')
  def _regexpdisplay(self, args):
    self.ctrl.do_command("_regexp-display", ' '.join(args))

  @neovim.command('LLregexpundisplay', nargs='*', complete='custom,LLComplete')
  def _regexpundisplay(self, args):
    self.ctrl.do_command("_regexp-undisplay", ' '.join(args))

  @neovim.command('LLregexpup', nargs='*', complete='custom,LLComplete')
  def _regexpup(self, args):
    self.ctrl.do_command("_regexp-up", ' '.join(args))

  @neovim.command('LLregister', nargs='*', complete='custom,LLComplete')
  def _register(self, args):
    self.ctrl.do_command("register", ' '.join(args))

  @neovim.command('LLscript', nargs='*', complete='custom,LLComplete')
  def _script(self, args):
    self.ctrl.do_command("script", ' '.join(args))

  @neovim.command('LLsettings', nargs='*', complete='custom,LLComplete')
  def _settings(self, args):
    self.ctrl.do_command("settings",' '.join(args))

  @neovim.command('LLsource', nargs='*', complete='custom,LLComplete')
  def _source(self, args):
    self.ctrl.do_command("source", ' '.join(args))

  @neovim.command('LLtarget', nargs='*', complete='custom,LLComplete')
  def _target(self, args):
    self.ctrl.do_target(' '.join(args))

  @neovim.command('LLthread', nargs='*', complete='custom,LLComplete')
  def _thread(self, args):
    self.ctrl.do_select("thread", ' '.join(args))

  @neovim.command('LLtype', nargs='*', complete='custom,LLComplete')
  def _type(self, args):
    self.ctrl.do_command("type", ' '.join(args))

  @neovim.command('LLversion', nargs='*', complete='custom,LLComplete')
  def _version(self, args):
    self.ctrl.do_command("version", ' '.join(args))

  @neovim.command('LLwatchpoint', nargs='*', complete='custom,LLComplete')
  def _watchpoint(self, args):
    self.ctrl.do_command("watchpoint", ' '.join(args))

  @neovim.command('LLup', nargs='?', complete='custom,LLComplete')
  def _up(self, args):
    self.ctrl.do_command("up", ' '.join(args), print_on_success=False, goto_file=True)

  @neovim.command('LLdown', nargs='?', complete='custom,LLComplete')
  def _down(self, args):
    self.ctrl.do_command("down", ' '.join(args), print_on_success=False, goto_file=True)

  @neovim.command('LLstepinst')
  def _stepinst(self):
    self.ctrl.do_step(StepType.INSTRUCTION)

  @neovim.command('LLstepinstover')
  def _stepinstover(self):
    self.ctrl.do_step(StepType.INSTRUCTION_OVER)

  @neovim.command('LLstepin')
  def _stepin(self):
    self.ctrl.do_step(StepType.INTO)

  @neovim.command('LLstep')
  def _step(self):
    self.ctrl.do_step(StepType.INTO)

  @neovim.command('LLnext')
  def _next(self):
    self.ctrl.do_step(StepType.OVER)

  @neovim.command('LLfinish')
  def _finish(self):
    self.ctrl.do_step(StepType.OUT)
