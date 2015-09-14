def resolve_line_entry(le):
  return (le.file.fullpath, le.line)

def get_pc_source_loc(thread):
  """ Returns a tuple (thread_index, file, line, column) that represents where
      the PC sign should be placed for a thread.
  """

  frame = thread.GetSelectedFrame()
  frame_num = frame.GetFrameID()
  le = frame.GetLineEntry()
  while not le.IsValid() and frame_num < thread.GetNumFrames():
    frame_num += 1
    le = thread.GetFrameAtIndex(frame_num).line_entry

  if le.IsValid():
    return (thread.GetIndexID(),) + resolve_line_entry(le)
  return None


def get_bploc_tuples(bp):
  """ Returns a list of tuples (filename, line) where a breakpoint was resolved. """
  if not bp.IsValid():
    return []
  locs = []
  for bploc in bp:
    le_tupl = resolve_line_entry(bploc.GetAddress().line_entry)
    if le_tupl[0] and le_tupl[1] > 0: # le_tupl[0] might be None
      locs.append(le_tupl)
  return locs

def get_description(lldb_obj):
  from lldb import SBStream
  s = SBStream()
  lldb_obj.GetDescription(s)
  return s.GetData()

def get_process_stat(target):
  from lldb import eStateStopped
  (proc, stat) = (None, '')
  if not target or not target.IsValid():
    stat = 'Target does not exist.'
  else:
    proc = target.GetProcess()
    if not proc or not proc.IsValid():
      proc = None
      stat = 'Process does not exist.'
    elif proc.GetState() == eStateStopped:
      pass
    else:
      stat = get_description(proc)
      exit_status = proc.GetExitStatus()
      if exit_status != -1:
        stat += ', exit status = %d' % exit_status
  return (proc, stat)
