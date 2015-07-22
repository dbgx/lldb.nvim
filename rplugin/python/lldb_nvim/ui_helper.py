def resolve_line_entry(le):
  # path = os.path.join(le.GetFileSpec().GetDirectory(), le.GetFileSpec().GetFilename())
  return (le.GetFileSpec().fullpath, le.GetLine(), le.GetColumn())

def get_pc_source_loc(thread):
  """ Returns a tuple (thread_index, file, line, column) that represents where
      the PC sign should be placed for a thread.
  """

  frame = thread.GetSelectedFrame()
  frame_num = frame.GetFrameID()
  le = frame.GetLineEntry()
  while not le.IsValid() and frame_num < thread.GetNumFrames():
    frame_num += 1
    le = thread.GetFrameAtIndex(frame_num).GetLineEntry()

  if le.IsValid():
    return (thread.GetIndexID(),) + resolve_line_entry(le)
  return None


def get_bploc_tuples(bp, logger):
  """ Returns a list of tuples (resolved, filename, line) where a breakpoint was resolved. """
  if not bp.IsValid():
    logger("breakpoint is invalid, no locations")
    return []
  locs = []
  numLocs = bp.GetNumLocations()
  for i in range(numLocs):
    bploc = bp.GetLocationAtIndex(i)
    resolved = bploc.IsResolved()

    le_tupl = resolve_line_entry(bploc.GetAddress().GetLineEntry())
    tupl = (resolved,) + le_tupl[:-1]

    locs.append(tupl)
  return locs

def get_process_stat(target):
  from lldb import eStateStopped
  (proc, stat) = (None, '')
  if not target or not target.IsValid():
    stat = 'Target does not exist.'
  else:
    proc = target.GetProcess()
    if not proc or not proc.IsValid():
      stat = 'Process does not exist.'
    elif proc.GetState() == eStateStopped:
      pass
    else:
      from lldb import SBStream
      s = SBStream()
      proc.GetDescription(s)
      stat = '%s, exit status = %s' % (s.GetData(), proc.GetExitStatus())
  return (proc, stat)

def get_command_content(args, target, commander):
  """ Returns the output of a command might rely on the process being stopped.
      If the process is not in 'stopped' state, return the command output
      only if the command succeeds, otherwise the process status is returned.
  """
  (proc, stat) = get_process_stat(target)
  (success, output) = commander(*args)
  if stat != '' and not success:
    output = stat
  return output.split('\n')

def get_selected_frame(process):
  thread = process.GetSelectedThread()
  if thread is None or not thread.IsValid():
    return None

  frame = thread.GetSelectedFrame()
  if frame is None or not frame.IsValid():
    return None

  return frame

def format_variable(var, indent = 0):
  """ Returns a list of strings "(Type) Name = Value" for SBValue var and
      its children
  """
  MAX_DEPTH = 6 # FIXME add user customizability

  val = var.GetValue() # returns None if the value is too big
  if val is None:
    val = '...'
  children = []
  if var.GetNumChildren() > 0:
    if indent >= MAX_DEPTH:
      children = [ '%s...' % (' ' * (indent + 1)) ]
    else:
      for x in var:
        children.extend(format_variable(x, indent + 1))
  return [ '%s(%s) %s = %s' % (' ' * indent,
                               var.GetTypeName(),
                               var.GetName(),
                               str(val)) ] + children

def get_locals_content(target):
  """ Returns list of local variables and their values in frame """
  (proc, stat) = get_process_stat(target)
  if stat != '':
    return [ stat ]
  frame = get_selected_frame(proc)
  if frame is None:
    return [ 'A valid frame does not exist!' ]

  # args, locals, statics, in-scope only # FIXME add user customizability
  vals = frame.GetVariables(True, True, False, True)
  out = []
  for x in vals:
    out.extend(format_variable(x))
  return out

def format_register(reg):
  """ Returns a tuple of strings "name = value" for SBRegister reg. """
  name = reg.GetName()
  val = reg.GetValue()
  if val is None:
    val = '...'
  return "%s = %s" % (name, val.strip())

def get_registers_content(target):
  """ Returns a list of registers in frame """
  (proc, stat) = get_process_stat(target)
  if stat != '':
    return [ stat ]
  frame = get_selected_frame(proc)
  if frame is None:
    return [ 'A valid frame does not exist!' ]

  result = []
  for register_set in frame.GetRegisters():
    # hack the register set name into the list of registers...
    result.append(' == %s ==' % register_set.GetName())
    for reg in register_set:
      result.append(format_register(reg))

  return result
