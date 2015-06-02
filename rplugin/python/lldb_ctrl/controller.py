import os, re, sys
import lldb

from vim_ui import UI

class StepType:
  INSTRUCTION = 1
  INSTRUCTION_OVER = 2
  INTO = 3
  OVER = 4
  OUT = 5

class LLController(object):
  """ Handles LLDB events and commands. """

  # Timeout (sec) for waiting on new events. Due to the current single threaded design,
  # we should wait a few seconds for any new event, and update vim buffers. After which,
  # the user will have to manually request an update (using :LLrefresh).
  eventDelay = 2 # FIXME see processPendingEvents()

  def __init__(self, vifx):
    """ Creates the LLDB SBDebugger object and initializes the UI class.
        vifx represents the parent LLInterface object.
    """
    self.target = None
    self.process = None
    self.load_dependent_modules = True

    self.dbg = lldb.SBDebugger.Create()
    self.command_interpreter = self.dbg.GetCommandInterpreter()

    self.vifx = vifx
    self.ui = UI(vifx)

  def complete_command(self, arg, line, pos):
    """ Returns a list of viable completions for line, and cursor at pos. """

    result = lldb.SBStringList()
    num = self.command_interpreter.HandleCompletion(line, pos, 1, -1, result)

    if num == -1:
      # FIXME: insert completion character... what's a completion character?
      pass
    elif num == -2:
      # FIXME: replace line with result.GetStringAtIndex(0)
      pass

    if result.GetSize() > 0:
      results =  filter(None, [result.GetStringAtIndex(x) for x in range(result.GetSize())])
      return results
    else:
      return []

  def update_ui(self, status='', goto_file=False, buf=None):
    """ Update lldb buffers and signs placed in source files.
        @param status
            The message to be printed on success on the vim status line.
        @param goto_file
            Whether or not to move the cursor to the program counter (PC).
        @param buf
            If None, all buffers and signs excepts breakpoints would be updated.
            If '!all', all buffers incl. breakpoints would be updated.
            Otherwise, update only the specified buffer.
    """
    excl = ['breakpoints']
    commander = self.get_command_result
    if buf is None:
      self.ui.update(self.target, commander, status, goto_file, excl)
    elif buf == '!all':
      self.ui.update(self.target, commander, status, goto_file)
    else:
      self.ui.update_buffer(buf, self.target, commander)

  def do_frame(self, args):
    """ Handle 'frame' command. """
    self.exec_command("frame", args)
    if args.startswith('s'): # select
      self.update_ui(goto_file=True)

  def do_thread(self, args):
    """ Handle 'thread' command. """
    self.exec_command("thread", args)
    if args.startswith('se'): # select
      self.update_ui(goto_file=True)
    elif args[0] not in list('bil'): # not in backtrace, info, list
      self.processPendingEvents(self.eventDelay)

  def do_process(self, args):
    """ Handle 'process' command. """
    # FIXME use do_attach/do_detach to handle attach/detach subcommands.
    if args.startswith("la"): # launch
      if self.process is not None and self.process.IsValid():
        pid = self.process.GetProcessID()
        self.process.Destroy()

      (success, result) = self.get_command_result("process", args)
      self.process = self.target.process
      if not success:
        self.vifx.log("Error during launch: " + str(result))
        return

      # launch succeeded, store pid and add some event listeners
      self.pid = self.process.GetProcessID()
      self.processListener = lldb.SBListener("process_event_listener")
      self.process.GetBroadcaster().AddListener(self.processListener, lldb.SBProcess.eBroadcastBitStateChanged)

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
      if not self.process.Destroy().Success():
        self.vifx.log("Error during kill: " + str(error))
      else:
        self.vifx.log("Killed process (pid=%d)" % self.pid)
    else:
      self.exec_command("process", args)

    self.processPendingEvents(self.eventDelay)

  def do_attach(self, process_name):
    """ Handle process attach. """
    (success, result) = self.get_command_result("attach", args)
    self.target = self.dbg.GetSelectedTarget()
    if not success:
      self.vifx.log("Error during attach: " + str(result))
      return

    # attach succeeded, initialize variables, listeners
    self.process = self.target.process
    self.pid = self.process.GetProcessID()
    self.processListener = lldb.SBListener("process_event_listener")
    self.process.GetBroadcaster().AddListener(self.processListener, lldb.SBProcess.eBroadcastBitStateChanged)
    self.vifx.log(str(result), 0)

  def do_detach(self):
    """ Handle process detach. """
    if self.process is not None and self.process.IsValid():
      pid = self.process.GetProcessID()
      self.process.Detach()
      self.processPendingEvents(self.eventDelay)

  def do_target(self, args):
    """ Handle 'target' command. """
    (success, result) = self.get_command_result("target", args)
    if not success:
      self.vifx.log(str(result))
    elif args.startswith('c'): # create
      self.target = self.dbg.GetSelectedTarget()
      self.vifx.log(str(result), 0)
      self.processPendingEvents(self.eventDelay)

  def do_command(self, args):
    """ Handle 'command' command. """
    self.ctrl.exec_command("command", args)
    if args.startswith('so'): # source
      self.processPendingEvents(self.eventDelay)
      self.update_ui(buf='breakpoints')

  def do_breakswitch(self, bufnr, line):
    """ Switch breakpoint at the specified line in the buffer. """
    key = (bufnr, line)
    if self.ui.bp_list.has_key(key):
      bps = self.ui.bp_list[key]
      args = "delete %s" % " ".join([str(b.GetID()) for b in bps])
    else:
      path = self.vifx.get_buffer_from_nr(bufnr).name
      args = "set -f %s -l %d" % (path, line)
    self.do_breakpoint(args)

  def do_breakpoint(self, args):
    """ Handle breakpoint command with command interpreter. """
    self.exec_command("breakpoint", args)
    self.update_ui(buf="breakpoints")

  def do_refresh(self):
    """ Process pending events and update UI on request. """
    status = self.processPendingEvents()

  def do_exit(self):
    """ Destroy the debugger instance. """
    self.dbg.Terminate()
    self.dbg = None

  def get_command_result(self, command, args=""):
    """ Run command in the command interpreter and returns (success, output) """
    result = lldb.SBCommandReturnObject()
    cmd = "%s %s" % (command, args)

    self.command_interpreter.HandleCommand(cmd, result)
    return (result.Succeeded(), result.GetOutput() if result.Succeeded() else result.GetError())

  def exec_command(self, command, args, update_level=0, goto_file=False):
    """ Run command in the interpreter and:
        + Print result on the vim status line (update_level >= 0)
        + Update UI (update_level >= 1)
        + Check for and process any lldb events in queue (update_level >= 2)
    """
    (success, output) = self.get_command_result(command, args)
    if success:
      if update_level == 0 and len(output) > 0:
        self.vifx.log(output, 0)
      if update_level == 1:
        self.update_ui(output, goto_file)
      elif update_level > 1:
        self.processPendingEvents(self.eventDelay, goto_file)
    else:
      self.vifx.log(output)

  def processPendingEvents(self, wait_seconds=0, goto_file=True): # FIXME replace this with a separate thread
    """ Handle any events that are queued from the inferior.
        Blocks for at most wait_seconds, or if wait_seconds == 0,
        process only events that are already queued.
    """

    num_events_handled = 0

    if self.process is not None:
      event = lldb.SBEvent()
      old_state = self.process.GetState()
      new_state = None
      done = False
      if old_state == lldb.eStateInvalid or old_state == lldb.eStateExited:
        # Early-exit if we are in 'boring' states
        pass
      else:
        while not done and self.processListener is not None:
          if not self.processListener.PeekAtNextEvent(event):
            if wait_seconds > 0:
              # No events on the queue, but we are allowed to wait for wait_seconds
              # for any events to show up.
              self.processListener.WaitForEvent(wait_seconds, event)
              new_state = lldb.SBProcess.GetStateFromEvent(event)

              num_events_handled += 1

            done = not self.processListener.PeekAtNextEvent(event)
          else:
            # An event is on the queue, process it here.
            self.processListener.GetNextEvent(event)
            new_state = lldb.SBProcess.GetStateFromEvent(event)

            # continue if stopped after attaching
            if old_state == lldb.eStateAttaching and new_state == lldb.eStateStopped:
              self.process.Continue()

            # If needed, perform any event-specific behaviour here
            num_events_handled += 1

    self.update_ui(goto_file=goto_file, buf='!all')

