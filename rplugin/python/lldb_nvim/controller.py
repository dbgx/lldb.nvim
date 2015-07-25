import os, sys
import lldb
from threading import Thread

from .vim_buffers import VimBuffers

class Controller(Thread):
  """ Handles LLDB events and commands. """

  CTRL_VOICE = 238 # just a number of my choice
  def __init__(self, vimx):
    """ Creates the LLDB SBDebugger object and initializes the VimBuffers class. """
    from Queue import Queue
    import logging
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)

    self.target = None
    self.process = None
    self.in_queue = Queue()
    self.out_queue = Queue()

    self.dbg = lldb.SBDebugger.Create()
    self.interpreter = self.dbg.GetCommandInterpreter()

    self.listener = lldb.SBListener("the_ear")
    self.interrupter = lldb.SBBroadcaster("the_mouth")
    self.interrupter.AddListener(self.listener, self.CTRL_VOICE)

    self.vimx = vimx # represents the parent Middleman object
    self.buffers = VimBuffers(vimx)
    super(Controller, self).__init__()

  def safe_call(self, method, args=[], sync=False): # safe_ marks thread safety
    if self.dbg is None:
      self.logger.critical("Debugger was terminated!" +
          (" Attempted calling %s" % method.func_name if method else ""))
      return
    self.in_queue.put((method, args, sync))
    interrupt = lldb.SBEvent(self.CTRL_VOICE, "the_sound")
    self.interrupter.BroadcastEvent(interrupt)
    if sync: # DECIDE timeout?
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

  def update_buffers(self, jump2pc=True, buf=None):
    """ Update lldb buffers and signs placed in source files.
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
      self.buffers.update(self.target, commander, jump2pc, excl)
    elif buf == '!all':
      self.buffers.update(self.target, commander, jump2pc)
    else:
      self.buffers.update_buffer(buf, self.target, commander)

  def do_stop(self):
    """ End the debug session. """
    self.do_target("delete")

  def do_frame(self, args):
    """ Handle 'frame' command. """
    self.exec_command("frame", args)
    if args.startswith('s'): # select
      self.update_buffers()

  def do_thread(self, args):
    """ Handle 'thread' command. """
    self.exec_command("thread", args)
    if args.startswith('se'): # select
      self.update_buffers()

  def do_process(self, args):
    """ Handle 'process' command. """
    # FIXME use do_attach/do_detach to handle attach/detach subcommands.
    if args.startswith("la"): # launch
      if self.process is not None and self.process.IsValid():
        self.process.Destroy()

      (success, result) = self.get_command_result("process", args)
      if not success:
        self.vimx.log("Error during launch: " + str(result))
        return
      self.process = self.target.process

      # launch succeeded, store pid and add some event listeners
      self.process.GetBroadcaster().AddListener(self.listener, lldb.SBProcess.eBroadcastBitStateChanged)

      self.vimx.log("%s" % result, 0)
    elif args.startswith("i"): # interrupt
      if not self.process or not self.process.IsValid():
        self.vimx.log("No valid process to interrupt.")
        return
      self.process.SendAsyncInterrupt()
    elif args.startswith("k"): # kill
      if not self.process or not self.process.IsValid():
        self.vimx.log("No valid process to kill.")
        return
      pid = self.process.GetProcessID()
      if not self.process.Destroy().Success():
        self.vimx.log("Error during kill: " + str(error))
      else:
        self.vimx.log("Killed process (pid=%d)" % pid)
    else:
      self.exec_command("process", args)

  def do_target(self, args):
    """ Handle 'target' command. """
    (success, result) = self.get_command_result("target", args)
    if not success:
      self.vimx.log(str(result))
    elif args.startswith('c'): # create
      self.target = self.dbg.GetSelectedTarget()
      self.vimx.log(str(result), 0)
      if len(self.buffers.bp_signs) > 0: # FIXME remove in favor of configuration file
        bp_bufs = dict(self.buffers.bp_signs.keys()).keys()
        def bpfile_mapper(b):
          if b.number in bp_bufs:
            return (b.number, b.name)
        bp_filemap = dict(self.vimx.map_buffers(bpfile_mapper)[:-1])
        for bufnr, line in self.buffers.bp_signs.keys():
          self.exec_command("breakpoint", "set -f %s -l %d" % (bp_filemap[bufnr], line))
      self.update_buffers(buf='breakpoints')
    elif args.startswith('d'): # delete
      self.target = None
      self.process = None
      self.vimx.log(str(result), 0)
      self.update_buffers(buf='!all')

  def do_attach(self, process_name):
    """ Handle process attach. """
    (success, result) = self.get_command_result("attach", args)
    self.target = self.dbg.GetSelectedTarget()
    if not success:
      self.vimx.log("Error during attach: " + str(result))
      return

    # attach succeeded, initialize variables, listeners
    self.process = self.target.process
    self.process.GetBroadcaster().AddListener(self.listener, lldb.SBProcess.eBroadcastBitStateChanged)
    self.vimx.log(str(result), 0)

  def do_detach(self):
    """ Handle process detach. """
    if self.process is not None and self.process.IsValid():
      self.process.Detach()

  def do_command(self, args):
    """ Handle 'command' command. """
    self.ctrl.exec_command("command", args)
    if args.startswith('so'): # source
      self.update_buffers(buf='breakpoints')

  def do_disassemble(self, args):
    self.buffers._content_map['disassembly'][1][1] = args
    self.update_buffers(buf='disassembly')

  def do_breakswitch(self, bufnr, line):
    """ Switch breakpoint at the specified line in the buffer. """
    key = (bufnr, line)
    if self.buffers.bp_list.has_key(key):
      bps = self.buffers.bp_list[key]
      args = "delete %s" % " ".join([str(b.GetID()) for b in bps])
    else:
      path = self.vimx.get_buffer_name(bufnr)
      args = "set -f %s -l %d" % (path, line)
    self.do_breakpoint(args)

  def do_breakpoint(self, args):
    """ Handle breakpoint command with command interpreter. """
    self.exec_command("breakpoint", args)
    self.update_buffers(buf="breakpoints")

  def get_command_result(self, command, args=""):
    """ Run command in the command interpreter and returns (success, output) """
    result = lldb.SBCommandReturnObject()
    cmd = "%s %s" % (command, args)

    self.interpreter.HandleCommand(cmd, result)
    return (result.Succeeded(), result.GetOutput() if result.Succeeded() else result.GetError())

  def exec_command(self, command, args, show_result=True, jump2pc=False):
    """ Run command in interpreter and possibly log the result as a vim message """
    (success, output) = self.get_command_result(command, args)
    if not success:
      self.vimx.log(output)
    elif show_result and len(output) > 0:
      self.vimx.log(output, 0)

  def run(self):
    import traceback
    from Queue import Empty
    to_count = 0
    while True:
      event = lldb.SBEvent()
      if self.listener.WaitForEvent(30, event): # 30 second timeout
        if event.GetType() == self.CTRL_VOICE:
          try:
            method, args, sync = self.in_queue.get(False)
            if method is None:
              break
            self.logger.info('Calling %s with %s' % (method.func_name, repr(args)))
            ret = method(*args)
            if sync:
              self.out_queue.put(ret)
          except Empty:
            self.logger.info('Empty interrupt!')
          except Exception:
            self.logger.critical(traceback.format_exc())
        else:
          while self.listener.PeekAtNextEvent(event) and event.GetType() != self.CTRL_VOICE:
            self.listener.GetNextEvent(event) # try to prevent flickering
          self.update_buffers(buf='!all')
      else: # Timed out
        to_count += 1
        if to_count > 172800: # 60 days worth idleness! barrier to prevent infinite loop
          self.logger.critical('Broke the loop barrier!')
          break
    self.dbg.Terminate()
    self.dbg = None
    self.logger.info('Terminated!')
