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
    self.ctrl = LLController()
    vim.command('au VimLeavePre * call LLExit()')

  @neovim.function('LLBreakswitch', sync=True)
  def ll_breakswitch(self, args):
    if len(args) != 2:
      vim.command('echom "LLBreakswitch requires exactly 2 arguments."')
      return
    self.ctrl.do_breakswitch(args[0], args[1])

  @neovim.function('LLComplete', sync=True)
  def ll_complete(self, args):
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
  def ll_exit(self):
    self.ctrl.do_exit()

  @neovim.command('LLuiInit')
  def ll_ui_init(self):
    buf_map = self.vim.eval('LLUpdateLayout()')
    self.ctrl.ui_init(self.vim, buf_map)

  @neovim.command('LLrun', nargs='*') # launch info can be passed ??
  def ll_run(self, args):
    self.ctrl.do_launch(False, ' '.join(args))

  @neovim.command('LLstart', nargs='*')
  def ll_start(self, args):
    self.ctrl.do_launch(True, ' '.join(args))

  @neovim.command('LLattach', nargs='1')
  def ll_attach(self, args):
    self.ctrl.do_attach(' '.join(args))

  @neovim.command('LLdetach')
  def ll_detach(self):
    self.ctrl.do_detach()

  @neovim.command('LLapropos', nargs='*', complete='custom,LLComplete')
  def ll_apropos(self, args):
    self.ctrl.do_command("apropos", ' '.join(args))

  @neovim.command('LLbacktrace', nargs='*', complete='custom,LLComplete')
  def ll_backtrace(self, args):
    self.ctrl.do_command("bt", ' '.join(args))

  @neovim.command('LLbreakpoint', nargs='*', complete='custom,LLComplete')
  def ll_breakpoint(self, args):
    self.ctrl.do_breakpoint(' '.join(args))

  @neovim.command('LLcommand', nargs='*', complete='custom,LLComplete')
  def ll_command(self, args):
    self.ctrl.do_command("command", ' '.join(args))

  @neovim.command('LLdisassemble', nargs='*', complete='custom,LLComplete')
  def ll_disassemble(self, args):
    self.ctrl.do_command("disassemble", ' '.join(args))

  @neovim.command('LLexpression', nargs='*', complete='custom,LLComplete')
  def ll_expression(self, args):
    self.ctrl.do_command("expression", ' '.join(args))

  @neovim.command('LLhelp', nargs='*', complete='custom,LLComplete')
  def ll_help(self, args):
    self.ctrl.do_command("help", ' '.join(args))

  @neovim.command('LLlog', nargs='*', complete='custom,LLComplete')
  def ll_log(self, args):
    self.ctrl.do_command("log", ' '.join(args))

  @neovim.command('LLplatform', nargs='*', complete='custom,LLComplete')
  def ll_platform(self, args):
    self.ctrl.do_command("platform",' '.join(args))

  @neovim.command('LLplugin', nargs='*', complete='custom,LLComplete')
  def ll_plugin(self, args):
    self.ctrl.do_command("plugin", ' '.join(args))

  @neovim.command('LLprocess', nargs='*', complete='custom,LLComplete')
  def ll_process(self, args):
    self.ctrl.do_process(' '.join(args))

  @neovim.command('LLregexpattach', nargs='*', complete='custom,LLComplete')
  def ll_regexpattach(self, args):
    self.ctrl.do_command("_regexp-attach", ' '.join(args))

  @neovim.command('LLregexpbreak', nargs='*', complete='custom,LLComplete')
  def ll_regexpbreak(self, args):
    self.ctrl.do_command("_regexp-break", ' '.join(args))

  @neovim.command('LLregexpbt', nargs='*', complete='custom,LLComplete')
  def ll_regexpbt(self, args):
    self.ctrl.do_command("_regexp-bt", ' '.join(args))

  @neovim.command('LLregexpdown', nargs='*', complete='custom,LLComplete')
  def ll_regexpdown(self, args):
    self.ctrl.do_command("_regexp-down", ' '.join(args))

  @neovim.command('LLregexptbreak', nargs='*', complete='custom,LLComplete')
  def ll_regexptbreak(self, args):
    self.ctrl.do_command("_regexp-tbreak", ' '.join(args))

  @neovim.command('LLregexpdisplay', nargs='*', complete='custom,LLComplete')
  def ll_regexpdisplay(self, args):
    self.ctrl.do_command("_regexp-display", ' '.join(args))

  @neovim.command('LLregexpundisplay', nargs='*', complete='custom,LLComplete')
  def ll_regexpundisplay(self, args):
    self.ctrl.do_command("_regexp-undisplay", ' '.join(args))

  @neovim.command('LLregexpup', nargs='*', complete='custom,LLComplete')
  def ll_regexpup(self, args):
    self.ctrl.do_command("_regexp-up", ' '.join(args))

  @neovim.command('LLregister', nargs='*', complete='custom,LLComplete')
  def ll_register(self, args):
    self.ctrl.do_command("register", ' '.join(args))

  @neovim.command('LLscript', nargs='*', complete='custom,LLComplete')
  def ll_script(self, args):
    self.ctrl.do_command("script", ' '.join(args))

  @neovim.command('LLsettings', nargs='*', complete='custom,LLComplete')
  def ll_settings(self, args):
    self.ctrl.do_command("settings",' '.join(args))

  @neovim.command('LLsource', nargs='*', complete='custom,LLComplete')
  def ll_source(self, args):
    self.ctrl.do_command("source", ' '.join(args))

  @neovim.command('LLtype', nargs='*', complete='custom,LLComplete')
  def ll_type(self, args):
    self.ctrl.do_command("type", ' '.join(args))

  @neovim.command('LLversion', nargs='*', complete='custom,LLComplete')
  def ll_version(self, args):
    self.ctrl.do_command("version", ' '.join(args))

  @neovim.command('LLwatchpoint', nargs='*', complete='custom,LLComplete')
  def ll_watchpoint(self, args):
    self.ctrl.do_command("watchpoint", ' '.join(args))

  @neovim.command('LLprint', nargs='*', sync=True, complete='custom,LLComplete') # eval='expand("<cword>")', sync=False
  def ll_print(self, args):
    self.ctrl.do_command("print", vim.eval("LLCursorWord(<args>)"))

  @neovim.command('LLpo', nargs='*', sync=True, complete='custom,LLComplete') # eval='expand("<cword>")', sync=False
  def ll_po(self, args):
    self.ctrl.do_command("po", vim.eval("LLCursorWord(<args>)"))

  @neovim.command('LLpO', nargs='*', sync=True, complete='custom,LLComplete') # eval='expand("<cWORD>")', sync=False
  def ll_pO(self, args):
    self.ctrl.do_command("po", vim.eval("LLCursorWORD(<args>)"))

  @neovim.command('LLframe', nargs='*', complete='custom,LLComplete')
  def ll_frame(self, args):
    self.ctrl.do_select("frame", ' '.join(args))

  @neovim.command('LLup', nargs='?', complete='custom,LLComplete')
  def ll_up(self, args):
    self.ctrl.do_command("up", ' '.join(args), print_on_success=False, goto_file=True)

  @neovim.command('LLdown', nargs='?', complete='custom,LLComplete')
  def ll_down(self, args):
    self.ctrl.do_command("down", ' '.join(args), print_on_success=False, goto_file=True)

  @neovim.command('LLthread', nargs='*', complete='custom,LLComplete')
  def ll_thread(self, args):
    self.ctrl.do_select("thread", ' '.join(args))

  @neovim.command('LLtarget', nargs='*', complete='custom,LLComplete')
  def ll_target(self, args):
    self.ctrl.do_target(' '.join(args))

  @neovim.command('LLcontinue')
  def ll_continue(self):
    self.ctrl.do_continue()

  @neovim.command('LLstepinst')
  def ll_stepinst(self):
    self.ctrl.do_step(StepType.INSTRUCTION)

  @neovim.command('LLstepinstover')
  def ll_stepinstover(self):
    self.ctrl.do_step(StepType.INSTRUCTION_OVER)

  @neovim.command('LLstepin')
  def ll_stepin(self):
    self.ctrl.do_step(StepType.INTO)

  @neovim.command('LLstep')
  def ll_step(self):
    self.ctrl.do_step(StepType.INTO)

  @neovim.command('LLnext')
  def ll_next(self):
    self.ctrl.do_step(StepType.OVER)

  @neovim.command('LLfinish')
  def ll_finish(self):
    self.ctrl.do_step(StepType.OUT)
