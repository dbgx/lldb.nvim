import lldb
from threading import Thread

from .vim_buffers import VimBuffers
from .session import Session

class Controller(Thread):
  """ Thread object that handles LLDB events and commands. """

  CTRL_VOICE = 238 # doesn't matter what this is
  TARG_NEW = 1
  TARG_DEL = 1 << 1
  PROC_NEW = 1 << 2
  PROC_DEL = 1 << 3
  BP_CHANGED = 1 << 4
  BAD_STATE = 1 << 5 # multiple targets

  def __init__(self, vimx):
    """ Creates the LLDB SBDebugger object and more! """
    from Queue import Queue
    import logging
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)

    self._dbg = lldb.SBDebugger.Create()
    self._target = None
    self._process = None
    self._num_bps = 0
    self.interpreter = self._dbg.GetCommandInterpreter()

    self.in_queue = Queue()
    self.out_queue = Queue()

    self.listener = lldb.SBListener("the_ear")
    self.interrupter = lldb.SBBroadcaster("the_mouth")
    self.interrupter.AddListener(self.listener, self.CTRL_VOICE)

    self.vimx = vimx # represents the parent Middleman object
    self.busy_stack = 0 # when busy > 0, buffers are not updated
    self.buffers = VimBuffers(vimx)
    self.session = Session(self, vimx)
    super(Controller, self).__init__()

  def is_busy(self):
    return self.busy_stack > 0

  def busy_more(self):
    self.busy_stack += 1

  def busy_less(self):
    self.busy_stack -= 1
    if self.busy_stack < 0:
      self.logger.critical("busy_stack < 0")
      self.busy_stack = 0

  def safe_call(self, method, args=[], sync=False, timeout=None): # threadsafe
    """ (Thread-safe) Call `method` with `args`. If `sync` is True, wait for
        `method` to complete and return its value. If timeout is set and non-
        negative, and the `method` did not complete within `timeout` seconds,
        a Queue.Empty exception is raised!
    """
    if self._dbg is None:
      self.logger.critical("Debugger was terminated!" +
          (" Attempted calling %s" % method.func_name if method else ""))
      return
    self.in_queue.put((method, args, sync))
    interrupt = lldb.SBEvent(self.CTRL_VOICE, "the_sound")
    self.interrupter.BroadcastEvent(interrupt)
    if sync:
      return self.out_queue.get(True, timeout)

  def safe_execute(self, tokens):
    """ (Thread-safe) Executes an lldb command defined by a list of tokens.
        If a token contains white-spaces, they are escaped using backslash.
    """
    cmd = ' '.join([ t.replace(' ', '\\ ') for t in tokens ])
    self.safe_call(self.exec_command, [cmd])

  def safe_exit(self):
    """ Exit from the event-loop, and wait for the thread to join.
        Should be called from outside this thread.
    """
    self.safe_call(None)
    self.join()

  def complete_command(self, arg, line, pos):
    """ Returns a list of viable completions for line, and cursor at pos. """
    pos = int(pos)
    result = lldb.SBStringList()

    if arg == line and line != '':
      # provide all possible completions when completing 't', 'b', 'di' etc.
      num = self.interpreter.HandleCompletion('', 0, 1, -1, result)
      cands = ['']
      for x in result:
        if x == line:
          cands.insert(1, x)
        elif x.startswith(line):
          cands.append(x)
    else:
      num = self.interpreter.HandleCompletion(line, pos, 1, -1, result)
      cands = [x for x in result]

    if len(cands) > 1:
      if cands[0] == '' and arg != '':
        if not cands[1].startswith(arg) or not cands[-1].startswith(arg):
          return []
      return cands[1:]
    else:
      return []

  def update_buffers(self, jump2pc=True, buf=None):
    """ Update lldb buffers and signs placed in source files.
        @param jump2pc
            Whether or not to move the cursor to the program counter (PC).
        @param buf
            If None, all buffers and signs excepts breakpoints would be updated.
            Otherwise, update only the specified buffer.
    """
    if self.is_busy():
      return
    commander = self.get_command_result
    if buf is None:
      self.buffers.update(self._target, commander, jump2pc)
    else:
      self.buffers.update_buffer(buf, self._target, commander)

  def get_state_changes(self):
    """ Get a value representing target or process changes.
        If a target or process is new, add our listener to its broadcaster.
    """
    changes = 0
    if self._dbg.GetNumTargets() > 1:
      return self.BAD_STATE

    if self._target is None or not self._target.IsValid():
      target = self._dbg.GetSelectedTarget()
      if target.IsValid():
        changes = self.TARG_NEW
        self._target = target
      elif self._target is not None:
        changes = self.TARG_DEL
        self._target = None

    if self._target is None:
      if self._process is not None:
        changes |= self.PROC_DEL
        self._process = None
      if self._num_bps > 0:
        changes |= self.BP_CHANGED
        self._num_bps = 0
      return changes

    if self._process is None or not self._process.IsValid():
      process = self._target.process
      if process.IsValid():
        changes |= self.PROC_NEW
        self._process = process
        process.broadcaster.AddListener(self.listener,
            lldb.SBProcess.eBroadcastBitStateChanged | \
            lldb.SBProcess.eBroadcastBitSTDOUT | \
            lldb.SBProcess.eBroadcastBitSTDERR)
            # TODO STDOUT, STDERR
      elif self._process is not None:
        changes |= self.PROC_DEL
        self._process = None

    num_bps = self._target.GetNumBreakpoints()
    if self._num_bps != num_bps:
      # TODO what if one was added and another deleted?
      changes |= self.BP_CHANGED
      self._num_bps = num_bps
    # TODO Watchpoints

    return changes

  def do_disassemble(self, cmd):
    """ Change the `disassembly` buffer command and update it. """
    self.buffers._content_map['disassembly'][1] = cmd
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
    self.exec_command("breakpoint " + args)

  def put_stdin(self, instr):
    """ Call PutSTDIN() of process with instr. """
    if self._process is not None:
      self._process.PutSTDIN(instr)
    else:
      self.vimx.log('No active process!')

  def get_command_result(self, command, add2hist=False):
    """ Runs command in the interpreter and returns (success, output)
        Not to be called directly for commands which changes debugger state;
        use exec_command instead.
    """
    result = lldb.SBCommandReturnObject()

    self.interpreter.HandleCommand(command.encode('ascii', 'ignore'), result, add2hist)
    return (result.Succeeded(), result.GetOutput() if result.Succeeded() else result.GetError())

  def exec_command(self, command):
    """ Runs command in the interpreter, calls update_buffers, and display the
        result in the logs buffer. Returns True if succeeded.
    """
    self.session.new_command(command)
    (success, output) = self.get_command_result(command, True)
    lines = output.split('\n')
    if not success:
      self.buffers.logs_append([u'\u2717' + line for line in lines[:-1]] + lines[-1:])
    elif len(output) > 0:
      self.buffers.logs_append([u'\u2713' + line for line in lines[:-1]] + lines[-1:])

    state_changes = self.get_state_changes()
    if state_changes & self.TARG_NEW != 0:
      self.session.new_target(self._target)
    elif state_changes & self.BP_CHANGED != 0 and self._target is not None:
      self.session.bp_changed(self._target.breakpoint_iter())

    if state_changes != 0:
      self.update_buffers()
    return success

  def run(self):
    """ This thread's event loop. """
    import traceback
    from Queue import Empty
    to_count = 0
    while True:
      event = lldb.SBEvent()
      if self.listener.WaitForEvent(30, event): # 30 second timeout

        def event_matches(broadcaster, skip=True):
          if event.BroadcasterMatchesRef(broadcaster):
            if skip:
              while self.listener.GetNextEventForBroadcaster(broadcaster, event):
                pass
            return True
          return False

        if event_matches(self.interrupter, skip=False):
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
        elif event_matches(self._process.broadcaster):
          while True:
            # FIXME break out of infinite loops (buggy programs may hang Vim!)
            stdout = self._process.GetSTDOUT(256)
            # TODO stderr
            if len(stdout) == 0:
              break
            lines = stdout.replace('\r\n', '\n').split('\n')
            self.buffers.logs_append(lines)
          self.update_buffers()
      else: # Timed out
        to_count += 1
        if to_count > 172800: # 60 days worth idleness! barrier to prevent infinite loop
          self.logger.critical('Broke the loop barrier!')
          break
    self._dbg.Terminate()
    self._dbg = None
    self.logger.info('Terminated!')
