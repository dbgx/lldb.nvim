import os, sys
import lldb
from threading import Thread

from vim_ui import UI

class LLController(Thread):
  """ Handles LLDB events and commands. """

  CTRL_VOICE = 238 # just a number of my choice
  def __init__(self, vifx):
    """ Creates the LLDB SBDebugger object and initializes the UI class.
        vifx represents the parent LLInterface object.
    """
    from Queue import Queue
    self.target = None
    self.process = None
    self.in_queue = Queue()
    self.out_queue = Queue()

    self.dbg = lldb.SBDebugger.Create()
    self.interpreter = self.dbg.GetCommandInterpreter()
    self.listener = lldb.SBListener("the_ear")
    self.interrupter = lldb.SBBroadcaster("the_mouth")
    self.interrupter.AddListener(self.listener, self.CTRL_VOICE)

    self.vifx = vifx
    self.ui = UI(vifx)
    super(LLController, self).__init__()

  def safe_call(self, method, args=[], sync=False): # safe_ marks thread safety
    self.in_queue.put((method, args, sync))
    interrupt = lldb.SBEvent(self.CTRL_VOICE, "the_sound")
    self.interrupter.BroadcastEvent(interrupt)
    if sync:
      return self.out_queue.get(True)

  def safe_execute(self, cmd, args):
    self.safe_call(self.exec_command, [cmd, ' '.join(args)])

  def safe_exit(self):
    self.safe_call(None)
    self.join()

  def complete_command(self, arg, line, pos):
    """ Returns a list of viable completions for line, and cursor at pos. """
    result = lldb.SBStringList()
    num = self.interpreter.HandleCompletion(line, pos, 1, -1, result)

    if num == -2: # encountered history repeat character ?
      pass

    if result.GetSize() > 0:
      results = filter(None, (result.GetStringAtIndex(x) for x in range(result.GetSize())))
      return results
    else:
      return []

  def update_ui(self, jump2pc=True, buf=None, status=''):
    """ Update lldb buffers and signs placed in source files.
        @param status
            The message to be printed on success on the vim status line.
        @param jump2pc
            Whether or not to move the cursor to the program counter (PC).
        @param buf
            If None, all buffers and signs excepts breakpoints would be updated.
            If '!all', all buffers incl. breakpoints would be updated.
            Otherwise, update only the specified buffer.
    """
    excl = ['breakpoints']
    commander = self.get_command_result
    if buf is None:
      self.ui.update(self.target, commander, status, jump2pc, excl)
    elif buf == '!all':
      self.ui.update(self.target, commander, status, jump2pc)
    else:
      self.ui.update_buffer(buf, self.target, commander)

  def do_stop(self):
    """ End the debug session. """
    # FIXME preserve breakpoints
    self.do_target("delete")

  def do_frame(self, args):
    """ Handle 'frame' command. """
    self.exec_command("frame", args)
    if args.startswith('s'): # select
      self.update_ui()

  def do_thread(self, args):
    """ Handle 'thread' command. """
    self.exec_command("thread", args)
    if args.startswith('se'): # select
      self.update_ui()

  def do_process(self, args):
    """ Handle 'process' command. """
    # FIXME use do_attach/do_detach to handle attach/detach subcommands.
    if args.startswith("la"): # launch
      if self.process is not None and self.process.IsValid():
        self.process.Destroy()

      (success, result) = self.get_command_result("process", args)
      if not success:
        self.vifx.log("Error during launch: " + str(result))
        return
      self.process = self.target.process

      # launch succeeded, store pid and add some event listeners
      self.process.GetBroadcaster().AddListener(self.listener, lldb.SBProcess.eBroadcastBitStateChanged)

      self.vifx.log("%s" % result, 0)
    elif args.startswith("i"): # interrupt
      if not self.process or not self.process.IsValid():
        self.vifx.log("No valid process to interrupt.")
        return
      self.process.SendAsyncInterrupt()
    elif args.startswith("k"): # kill
      if not self.process or not self.process.IsValid():
        self.vifx.log("No valid process to kill.")
        return
      pid = self.process.GetProcessID()
      if not self.process.Destroy().Success():
        self.vifx.log("Error during kill: " + str(error))
      else:
        self.vifx.log("Killed process (pid=%d)" % pid)
    else:
      self.exec_command("process", args)

  def do_target(self, args):
    """ Handle 'target' command. """
    (success, result) = self.get_command_result("target", args)
    if not success:
      self.vifx.log(str(result))
    elif args.startswith('c'): # create
      self.target = self.dbg.GetSelectedTarget()
      self.vifx.log(str(result), 0)
      self.update_ui(buf='breakpoints')
    elif args.startswith('d'): # delete
      self.target = None
      self.process = None
      self.vifx.log(str(result), 0)
      self.update_ui(buf='!all')

  def do_attach(self, process_name):
    """ Handle process attach. """
    (success, result) = self.get_command_result("attach", args)
    self.target = self.dbg.GetSelectedTarget()
    if not success:
      self.vifx.log("Error during attach: " + str(result))
      return

    # attach succeeded, initialize variables, listeners
    self.process = self.target.process
    self.process.GetBroadcaster().AddListener(self.listener, lldb.SBProcess.eBroadcastBitStateChanged)
    self.vifx.log(str(result), 0)

  def do_detach(self):
    """ Handle process detach. """
    if self.process is not None and self.process.IsValid():
      self.process.Detach()

  def do_command(self, args):
    """ Handle 'command' command. """
    self.ctrl.exec_command("command", args)
    if args.startswith('so'): # source
      self.update_ui(buf='breakpoints')

  def do_breakswitch(self, bufnr, line):
    """ Switch breakpoint at the specified line in the buffer. """
    key = (bufnr, line)
    if self.ui.bp_list.has_key(key):
      bps = self.ui.bp_list[key]
      args = "delete %s" % " ".join([str(b.GetID()) for b in bps])
    else:
      path = self.vifx.get_buffer_name(bufnr)
      args = "set -f %s -l %d" % (path, line)
    self.do_breakpoint(args)

  def do_breakpoint(self, args):
    """ Handle breakpoint command with command interpreter. """
    self.exec_command("breakpoint", args)
    self.update_ui(buf="breakpoints")

  def get_command_result(self, command, args=""):
    """ Run command in the command interpreter and returns (success, output) """
    result = lldb.SBCommandReturnObject()
    cmd = "%s %s" % (command, args)

    self.interpreter.HandleCommand(cmd, result)
    return (result.Succeeded(), result.GetOutput() if result.Succeeded() else result.GetError())

  def exec_command(self, command, args, update_level=0, jump2pc=False):
    """ Run command in the interpreter and:
        + Print result on the vim status line (update_level >= 0)
        + Update UI (update_level >= 1)
    """
    (success, output) = self.get_command_result(command, args)
    if success:
      if update_level == 0 and len(output) > 0:
        self.vifx.log(output, 0)
      if update_level == 1:
        self.update_ui(jump2pc, status=output)
    else:
      self.vifx.log(output)

  def run(self):
    from Queue import Empty
    while True:
      event = lldb.SBEvent()
      if self.listener.WaitForEvent(8, event):
        if event.GetType() == self.CTRL_VOICE:
          try:
            method, args, sync = self.in_queue.get(False)
            if method is None:
              break
            self.vifx.logger.info('Calling %s with %s' % (method.func_name, repr(args)))
            ret = method(*args)
            if sync:
              self.out_queue.put(ret)
          except Empty:
            self.vifx.logger.info('Empty interrupt!')
        else:
          self.update_ui(buf='!all')
      else: # Timed out
        pass
    self.dbg.Terminate()
    self.dbg = None
    self.vifx.logger.info('Terminated!')
