
# Classes responsible for drawing signs in the Vim user interface.

class VimSign(object):
  SIGN_BREAKPOINT_RESOLVED = "llsign_bpres"
  SIGN_BREAKPOINT_UNRESOLVED = "llsign_bpunres"
  SIGN_PC_SELECTED = "llsign_pcsel"
  SIGN_PC_UNSELECTED = "llsign_pcunsel"

  # unique sign id (for ':sign place')
  sign_id = 100

  def __init__(self, vifx, name, bufnr, line):
    self.vifx = vifx
    self.id = VimSign.sign_id
    VimSign.sign_id += 1
    self.name = name
    self.bufnr = bufnr
    self.line = line
    self.show()

  def show(self):
    self.vifx.sign_place(self.id, self.name, self.bufnr, self.line)

  def hide(self):
    self.vifx.sign_unplace(self.id)

class BreakpointSign(VimSign):
  def __init__(self, vifx, bufnr, line, resolved):
    self.resolved = resolved
    name = VimSign.SIGN_BREAKPOINT_RESOLVED if resolved else VimSign.SIGN_BREAKPOINT_UNRESOLVED
    super(BreakpointSign, self).__init__(vifx, name, bufnr, line)

class PCSign(VimSign):
  def __init__(self, vifx, bufnr, line, selected):
    self.selected = selected
    name = VimSign.SIGN_PC_SELECTED if selected else VimSign.SIGN_PC_UNSELECTED
    super(PCSign, self).__init__(vifx, name, bufnr, line)
