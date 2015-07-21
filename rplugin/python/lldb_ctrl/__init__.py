import neovim
import check_lldb
from Queue import Queue

lldb_success = check_lldb.probe()

from .controller import LLController

@neovim.plugin
class LLInterface(object):
  def __init__(self, vim):
    self.vim = vim
    if not lldb_success:
      self.vifx.logger.critical('LLDB could not be imported!')
      # ImportError will be raised in LLController init below.
    self.ctrl = LLController(self)
    self.ctrl.start()
    vim.command('au VimLeavePre * call LLExit()')

    import logging
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)

  def safe_vim_eval(self, expr):
    vim = self.vim
    out_q = Queue()
    vim.session.threadsafe_call(lambda: out_q.put(vim.eval(expr)))
    return out_q.get()

  def safe_vim_command(self, cmd):
    vim = self.vim
    vim.session.threadsafe_call(lambda: vim.command(cmd))

  def log(self, msg, level=1):
    """ Execute echom in vim using appropriate highlighting. """
    level_map = ['None', 'WarningMsg', 'ErrorMsg']
    msg = msg.strip().replace('"', '\\"').replace('\n', '\\n')
    self.safe_vim_command('echohl %s | echom "%s" | echohl None' % (level_map[level], msg))

  def buffer_add(self, name):
    """ Create a buffer (if it doesn't exist) and return its number. """
    bufnr = self.safe_vim_eval('bufnr("%s", 1)' % name)
    self.safe_vim_command('call setbufvar(%d, "&bl", 1)' % bufnr)
    return bufnr

  def sign_jump(self, bufnr, sign_id):
    """ Try jumping to the specified sign_id in buffer with number bufnr. """
    self.safe_vim_command("call LLTrySignJump(%d, %d)" % (bufnr, sign_id))

  def sign_place(self, sign_id, name, bufnr, line):
    """ Place a sign at the specified location. """
    cmd = "sign place %d name=%s line=%d buffer=%s" % (sign_id, name, line, bufnr)
    self.safe_vim_command(cmd)

  def sign_unplace(self, sign_id):
    """ Hide a sign with specified id. """
    self.safe_vim_command("sign unplace %d" % sign_id)

  def map_buffers(self, fn):
    """ Does a map using fn callback on all buffer object and returns a list.
        @param fn: callback function which takes buffer object as a parameter.
                   If None is returned, the item is ignored.
                   If a StopIteration is raised, the loop breaks.
        @return: The last item in the list returned is a placeholder indicating:
                 * completed iteration, if None is present
                 * otherwise, if StopIteration was raised, the message would be the last item
    """
    vim = self.vim
    out_q = Queue(maxsize=1)
    def map_buffers_inner():
      mapped = []
      breaked = False
      for b in vim.buffers:
        try:
          ret = fn(b)
          if ret is not None:
            mapped.append(ret)
        except StopIteration as e:
          mapped.append(e.message)
          breaked = True
          break
      if not breaked:
        mapped.append(None)
      out_q.put(mapped)
    vim.session.threadsafe_call(map_buffers_inner)
    return out_q.get()

  def get_buffer_name(self, nr):
    """ Get the buffer name given its number. """
    def name_mapper(b):
      if b.number == nr:
        raise StopIteration(b.name)
    return self.map_buffers(name_mapper)[0]

  def buf_init(self):
    """ Create all lldb buffers and initialize the buffer map. """
    buf_map = self.safe_vim_eval('LLBuffersInit()')
    return buf_map

  @neovim.function('LLBreakswitch')
  def _breakswitch(self, args):
    if len(args) != 2:
      self.log('LLBreakswitch takes exactly 2 arguments (%d given)' % len(args))
    else:
      self.ctrl.safe_call(self.ctrl.do_breakswitch, [args[0], args[1]])

  @neovim.function('LLComplete', sync=True)
  def _complete(self, args):
    arg = args[0]
    line = args[1]
    pos = int(args[2])

    assert line[:2] == 'LL'
    # Remove first 'LL' characters that all commands start with
    line = line[2:]
    pos -= 2

    if line.startswith('regexp'):
      line = '_regexp-' + line.lstrip('regexp')
      pos += 2

    results = self.ctrl.safe_call(self.ctrl.complete_command, [arg, line, pos], True)
    return '%s\n' % '\n'.join(results)

  @neovim.function('LLExit', sync=True)
  def _exit(self, args):
    self.ctrl.safe_exit()

  @neovim.command('LLrefresh')
  def _refresh(self):
    self.ctrl.safe_call(self.ctrl.update_ui, [False, '!all'])

  @neovim.command('LLrun', nargs='*')
  def _run(self, args):
    # FIXME: Remove in favor of `LLprocess launch` and `LLstart`?
    self.ctrl.safe_call(self.ctrl.do_process, ['launch ' + ' '.join(args)])

  @neovim.command('LLstop')
  def _stop(self):
    self.ctrl.safe_call(self.ctrl.do_stop)
    self.safe_vim_command('call LLTabCheckClose(1)')

  @neovim.command('LLstart', nargs='*')
  def _start(self, args):
    # TODO: Take no arguments; launch as specified in the configuration file
    self.ctrl.safe_call(self.ctrl.do_process, ['launch -s ' + ' '.join(args)])

  @neovim.command('LLattach', nargs='1')
  def _attach(self, args):
    self.ctrl.safe_call(self.ctrl.do_attach, [' '.join(args)])

  @neovim.command('LLdetach')
  def _detach(self):
    self.ctrl.safe_call(self.ctrl.do_detach)

  @neovim.command('LLapropos', nargs='*', complete='custom,LLComplete')
  def _apropos(self, args):
    self.ctrl.safe_execute("apropos", args)

  @neovim.command('LLbreakpoint', nargs='*', complete='custom,LLComplete')
  def _breakpoint(self, args):
    self.ctrl.safe_call(self.ctrl.do_breakpoint, [' '.join(args)])

  @neovim.command('LLbt')
  def _bt(self):
    self.safe_vim_command('drop backtrace')

  @neovim.command('LLcommand', nargs='*', complete='custom,LLComplete')
  def _command(self, args):
    self.ctrl.safe_call(self.ctrl.do_command, [' '.join(args)])

  @neovim.command('LLcontinue', nargs='*', complete='custom,LLComplete')
  def _continue(self, args):
    self.ctrl.safe_execute("continue", args)

  @neovim.command('LLdisassemble', nargs='*', complete='custom,LLComplete')
  def _disassemble(self, args):
    self.ctrl.safe_call(self.ctrl.do_disassemble, [' '.join(args)])
    self.safe_vim_command('drop disassembly')

  @neovim.command('LLexpression', nargs='*', complete='custom,LLComplete')
  def _expression(self, args):
    self.ctrl.safe_execute("expression", args)

  @neovim.command('LLframe', nargs='*', complete='custom,LLComplete')
  def _frame(self, args):
    self.ctrl.safe_call(self.ctrl.do_frame, [' '.join(args)])

  @neovim.command('LLhelp', nargs='*', complete='custom,LLComplete')
  def _help(self, args):
    self.ctrl.safe_execute("help", args)

  @neovim.command('LLlog', nargs='*', complete='custom,LLComplete')
  def _log(self, args):
    self.ctrl.safe_execute("log", args)

  @neovim.command('LLplatform', nargs='*', complete='custom,LLComplete')
  def _platform(self, args):
    self.ctrl.safe_execute("platform", args)

  @neovim.command('LLplugin', nargs='*', complete='custom,LLComplete')
  def _plugin(self, args):
    self.ctrl.safe_execute("plugin", args)

  @neovim.command('LLpo', nargs='*', complete='custom,LLComplete')
  def _po(self, args):
    self.ctrl.safe_execute("po", args)

  @neovim.command('LLprint', nargs='*', complete='custom,LLComplete')
  def _print(self, args):
    self.ctrl.safe_execute("print", args)

  @neovim.command('LLprocess', nargs='*', complete='custom,LLComplete')
  def _process(self, args):
    self.ctrl.safe_call(self.ctrl.do_process, [' '.join(args)])

  @neovim.command('LLregexpattach', nargs='*', complete='custom,LLComplete')
  def _regexpattach(self, args):
    self.ctrl.safe_call(self.ctrl.do_attach, [' '.join(args)])

  @neovim.command('LLregexpbreak', nargs='*', complete='custom,LLComplete')
  def _regexpbreak(self, args):
    self.ctrl.safe_execute("_regexp-break", args)

  @neovim.command('LLregexpbt')
  def _regexpbt(self):
    self.safe_vim_command('drop backtrace')

  @neovim.command('LLregexptbreak', nargs='*', complete='custom,LLComplete')
  def _regexptbreak(self, args):
    self.ctrl.safe_execute("_regexp-tbreak", args)

  @neovim.command('LLregexpdisplay', nargs='*', complete='custom,LLComplete')
  def _regexpdisplay(self, args):
    self.ctrl.safe_execute("_regexp-display", args)

  @neovim.command('LLregexpundisplay', nargs='*', complete='custom,LLComplete')
  def _regexpundisplay(self, args):
    self.ctrl.safe_execute("_regexp-undisplay", args)

  @neovim.command('LLregister', nargs='*', complete='custom,LLComplete')
  def _register(self, args):
    self.ctrl.safe_execute("register", args)

  @neovim.command('LLscript', nargs='*', complete='custom,LLComplete')
  def _script(self, args):
    self.ctrl.safe_execute("script", args)

  @neovim.command('LLsettings', nargs='*', complete='custom,LLComplete')
  def _settings(self, args):
    self.ctrl.safe_execute("settings",args)

  @neovim.command('LLsource', nargs='*', complete='custom,LLComplete')
  def _source(self, args):
    self.ctrl.safe_execute("source", args)

  @neovim.command('LLtarget', nargs='*', complete='custom,LLComplete')
  def _target(self, args):
    self.ctrl.safe_call(self.ctrl.do_target, [' '.join(args)])

  @neovim.command('LLthread', nargs='*', complete='custom,LLComplete')
  def _thread(self, args):
    self.ctrl.safe_call(self.ctrl.do_thread, [' '.join(args)])

  @neovim.command('LLtype', nargs='*', complete='custom,LLComplete')
  def _type(self, args):
    self.ctrl.safe_execute("type", args)

  @neovim.command('LLversion', nargs='*', complete='custom,LLComplete')
  def _version(self, args):
    self.ctrl.safe_execute("version", args)

  @neovim.command('LLwatchpoint', nargs='*', complete='custom,LLComplete')
  def _watchpoint(self, args):
    self.ctrl.safe_execute("watchpoint", args)

  @neovim.command('LLup', nargs='?', complete='custom,LLComplete')
  def _up(self, args):
    n = "1" if len(args) == 0 else args[0]
    self.ctrl.safe_call(self.ctrl.do_frame, ['select -r +' + n])

  @neovim.command('LLdown', nargs='?', complete='custom,LLComplete')
  def _down(self, args):
    n = "1" if len(args) == 0 else args[0]
    self.ctrl.safe_call(self.ctrl.do_frame, ['select -r -' + n])

  @neovim.command('LLstep', nargs='*', complete='custom,LLComplete')
  def _step(self, args):
    self.ctrl.safe_execute("step", args)

  @neovim.command('LLnext', nargs='*', complete='custom,LLComplete')
  def _next(self, args):
    self.ctrl.safe_execute("next", args)

  @neovim.command('LLfinish', nargs='*', complete='custom,LLComplete')
  def _finish(self, args):
    self.ctrl.safe_execute("finish", args)
