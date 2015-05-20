
# LLDB UI state in the Vim user interface.
#
# FIXME: implement WatchlistPane to displayed watched expressions
# FIXME: define interface for interactive panes, like catching enter
#        presses to change selected frame/thread...
#

import os, re, sys
import lldb
import neovim
from vim_signs import *

# Shamelessly copy/pasted from lldbutil.py in the test suite
def get_description(obj, option=None):
  """Calls lldb_obj.GetDescription() and returns a string, or None.
  For SBTarget, SBBreakpointLocation, and SBWatchpoint lldb objects, an extra
  option can be passed in to describe the detailed level of description
  desired:
      o lldb.eDescriptionLevelBrief
      o lldb.eDescriptionLevelFull
      o lldb.eDescriptionLevelVerbose
  """
  method = getattr(obj, 'GetDescription')
  if not method:
    return None
  tuple = (lldb.SBTarget, lldb.SBBreakpointLocation, lldb.SBWatchpoint)
  if isinstance(obj, tuple):
    if option is None:
      option = lldb.eDescriptionLevelBrief

  stream = lldb.SBStream()
  if option is None:
    success = method(stream)
  else:
    success = method(stream, option)
  if not success:
    return None
  return stream.GetData()

def is_same_file(a, b):
  """ returns true if paths a and b are the same file """
  a = os.path.realpath(a)
  b = os.path.realpath(b)
  return a in b or b in a

class UI:
  def __init__(self, vim, buf_map):
    """ Declare UI state variables """
    self.vim = vim #neovim.attach('socket', path=socket)

    self.buffer_map = buf_map

    # map of tuples (filename, line) --> SBBreakpoint
    self.markedBreakpoints = {}

    # Currently shown signs
    self.breakpointSigns = {}
    self.pcSigns = []

  def log(self, msg, level=1):
    level_map = ['None', 'WarningMsg', 'ErrorMsg']
    msg = msg.replace('"', '\\"').replace('\n', '\\n')
    self.vim.command('echohl %s | echom "%s" | echohl None' % (level_map[level], msg,))

  def current_window(self):
    return self.vim.current.window

  def current_buffer(self):
    return self.vim.current.buffer

  def get_user_buffers(self, filter_name=None):
    """ Returns a list of buffers that are not a part of the LLDB UI.
    """
    ret = []
    for b in self.vim.buffers:
      if b.number not in self.buffer_map.keys(): #and self.vim.eval('buflisted( %d )' % b.number):
        if filter_name is None or filter_name in b.name:
          ret.append(b)
    return ret

  def update_pc(self, process, buffers, goto_file):
    """ Place the PC sign on the PC location of each thread's selected frame """

    def GetPCSourceLocation(thread):
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
        path = os.path.join(le.GetFileSpec().GetDirectory(), le.GetFileSpec().GetFilename())
        return (thread.GetIndexID(), path, le.GetLine(), le.GetColumn())
      return None


    # Clear all existing PC signs
    del_list = []
    for sign in self.pcSigns:
      sign.hide()
      del_list.append(sign)
    for sign in del_list:
      self.pcSigns.remove(sign)
      del sign

    # Show a PC marker for each thread
    for thread in process:
      loc = GetPCSourceLocation(thread)
      if not loc:
        # no valid source locations for PCs. hide all existing PC markers
        continue

      buf = None
      (tid, fname, line, col) = loc
      buffers = self.get_user_buffers(fname)
      is_selected = thread.GetIndexID() == process.GetSelectedThread().GetIndexID()
      if len(buffers) == 1:
        bufnr = buffers[0].number
      elif is_selected and os.path.exists(fname) and goto_file:
        vim.command('badd %s' % fname)
        bufnr = vim.eval('bufnr("%s")' % fname)
      elif len(buffers) > 1 and goto_file:
        #FIXME: multiple open buffers match PC location
        continue
      else:
        continue

      self.pcSigns.append(PCSign(self.vim, bufnr, line, is_selected))

      if is_selected and goto_file:
        # if the selected file has a PC marker, move the cursor there too
        curname = self.current_buffer().name
        if curname is not None and is_same_file(curname, fname):
          move_cursor(self.vim, line, 0)
        elif move_cursor:
          print "FIXME: not sure where to move cursor because %s != %s " % (self.current_buffer().name, fname)

  def update_breakpoints(self, target, buffers):
    """ Decorates buffer with signs corresponding to breakpoints in target. """

    def GetBreakpointLocations(bp):
      """ Returns a list of tuples (resolved, filename, line) where a breakpoint was resolved. """
      if not bp.IsValid():
        self.log("breakpoint is invalid, no locations")
        return []

      ret = []
      numLocs = bp.GetNumLocations()
      for i in range(numLocs):
        loc = bp.GetLocationAtIndex(i)
        desc = get_description(loc, lldb.eDescriptionLevelFull)
        match = re.search('at\ ([^:]+):([\d]+)', desc)
        try:
          lineNum = int(match.group(2).strip())
          ret.append((loc.IsResolved(), match.group(1), lineNum))
        except ValueError as e:
          self.log("unable to parse breakpoint location line number: '%s'\n%s" % (match.group(2), str(e),))

      return ret

    if target is None or not target.IsValid():
      return

    needed_bps = {}
    for bp_index in range(target.GetNumBreakpoints()):
      bp = target.GetBreakpointAtIndex(bp_index)
      locations = GetBreakpointLocations(bp)
      for (is_resolved, file, line) in GetBreakpointLocations(bp):
        for buf in buffers:
          if file in buf.name:
            needed_bps[(buf, line, is_resolved)] = bp

    # Hide any signs that correspond with disabled breakpoints
    del_list = []
    for (b, l, r) in self.breakpointSigns:
      if (b, l, r) not in needed_bps:
        self.breakpointSigns[(b, l, r)].hide()
        del_list.append((b, l, r))
    for d in del_list:
      del self.breakpointSigns[d]

    # Show any signs for new breakpoints
    for (b, l, r) in needed_bps:
      bp = needed_bps[(b, l, r)]
      if self.haveBreakpoint(b.name, l):
        self.markedBreakpoints[(b.name, l)].append(bp)
      else:
        self.markedBreakpoints[(b.name, l)] = [bp]

      if (b, l, r) not in self.breakpointSigns:
        s = BreakpointSign(self.vim, b, l, r)
        self.breakpointSigns[(b, l, r)] = s

  def update(self, target, status, controller, goto_file=False):
    """ Updates breakpoint/pc marks and prints status to the vim status line.
        If goto_file is True, the user's cursor is moved to the source PC location in the selected frame.
    """

    # FIXME Update debugger info panels
    self.update_breakpoints(target, self.get_user_buffers())

    if target is not None and target.IsValid():
      process = target.GetProcess()
      if process is not None and process.IsValid():
        self.update_pc(process, self.get_user_buffers, goto_file) # FIXME?

    if status is not None and len(status) > 0:
      print status

  def haveBreakpoint(self, file, line):
    """ Returns True if we have a breakpoint at file:line, False otherwise  """
    return (file, line) in self.markedBreakpoints

  def getBreakpoints(self, fname, line):
    """ Returns the LLDB SBBreakpoint object at fname:line """
    if self.haveBreakpoint(fname, line):
      return self.markedBreakpoints[(fname, line)]
    else:
      return None

  def deleteBreakpoints(self, name, line):
    del self.markedBreakpoints[(name, line)]

# vim:et:ts=2:sw=2
