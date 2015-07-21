
# Classes responsible for drawing signs in the Vim user interface.

class VimSign(object):
  SIGN_BREAKPOINT_RESOLVED = "llsign_bpres"
  SIGN_BREAKPOINT_UNRESOLVED = "llsign_bpunres"
  SIGN_PC_SELECTED = "llsign_pcsel"
  SIGN_PC_UNSELECTED = "llsign_pcunsel"

  # unique sign id (for ':sign place')
  sign_id = 100

  def __init__(self, vifx, name, bufnr, line, hidden):
    self.vifx = vifx
    self.id = VimSign.sign_id
    VimSign.sign_id += 1
    self.name = name
    self.bufnr = bufnr
    self.line = line
    if hidden:
      self.hidden = True
    else:
      self.show()

  def show(self):
    self.vifx.sign_place(self.id, self.name, self.bufnr, self.line)
    self.hidden = False

  def hide(self):
    self.vifx.sign_unplace(self.id)
    self.hidden = True

class BreakpointSign(VimSign):
  def __init__(self, vifx, bufnr, line, resolved, hidden=False):
    self.resolved = resolved
    name = VimSign.SIGN_BREAKPOINT_RESOLVED if resolved else VimSign.SIGN_BREAKPOINT_UNRESOLVED
    super(BreakpointSign, self).__init__(vifx, name, bufnr, line, hidden)

class PCSign(VimSign):
  def __init__(self, vifx, bufnr, line, selected, hidden=False):
    self.selected = selected
    name = VimSign.SIGN_PC_SELECTED if selected else VimSign.SIGN_PC_UNSELECTED
    super(PCSign, self).__init__(vifx, name, bufnr, line, hidden)
