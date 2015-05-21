from lldb import eStateStopped

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

    line_entry = bploc.GetAddress().GetLineEntry()
    path = line_entry.GetFileSpec().fullpath
    line = line_entry.GetLine()
    tupl = (resolved, path, line)

    locs.append(tupl)
  return locs

def get_command_content(args, target, commander):
  """ Returns the output of a command that relies on the process being stopped.
      If the process is not in 'stopped' state, the process status is returned.
  """
  output = ""
  if not target or not target.IsValid():
    output = "Target does not exist."
  elif not target.GetProcess() or not target.GetProcess().IsValid():
    output = "Process does not exist."
  elif target.GetProcess().GetState() == eStateStopped:
    (success, output) = commander(*args)
  else:
    (success, output) = commander("process", "status")
  return output

def format_variable(var, indent = 0):
  """ Returns a list of tuples of strings "(Type) Name", "Value" for SBValue var
      and its children
  """
  MAX_DEPTH = 6

  if indent > MAX_DEPTH:
    return []
  else:
    val = var.GetValue() # returns None if the value is too big
    if val is None:
      val = "..."
    children = []
    if var.GetNumChildren() > 0:
      for x in var:
        children.extend(format_variable(x, indent + 1))
    return [ ( "%s(%s) %s" % (' ' * indent, var.GetTypeName(), var.GetName()),
               str(val) ) ] + children

def get_locals_content(frame):
  """ Returns list of key-value pairs of local variables in frame """
  vals = frame.GetVariables(True, #arguments
                            True, #locals
                            False, #statics
                            True) #in-scope only # FIXME: customizability
  out = []
  for v in [format_variable(x) for x in vals]:
    out.extend(v)
  return out

def format_register(reg):
  """ Returns a tuple of strings ("name", "value") for SBRegister reg. """
  name = reg.GetName()
  val = reg.GetValue()
  if val is None:
    val = "..."
  return (name, val.strip())

def get_registers_content(frame):
  """ Returns a list of key-value pairs ("name", "value") of registers in frame """
  result = []
  for register_set in frame.GetRegisters():
    # hack the register set name into the list of registers...
    result.append((" == %s ==" % register_set.GetName(), ""))
    for reg in register_set:
      result.append(format_register(reg))
  return result

