
# Classes responsible for drawing signs in the Vim user interface.

class VimSign(object):
  SIGN_BREAKPOINT_RESOLVED = "ll_sign_bp_res"
  SIGN_BREAKPOINT_UNRESOLVED = "ll_sign_bp_unres"
  SIGN_PC = "ll_sign_pc"

  # unique sign id (for ':sign place')
  sign_id = 100

  def __init__(self, vifx, name, bufnr, line_number):
    self.vifx = vifx
    self.show(name, bufnr, line_number)

  def show(self, name, bufnr, line_number):
    self.id = VimSign.sign_id
    VimSign.sign_id += 1
    self.vifx.sign_place(self.id, name, bufnr, line_number)

  def hide(self):
    self.vifx.sign_unplace(self.id)

class BreakpointSign(VimSign):
  def __init__(self, vifx, bufnr, line_number, is_resolved):
    name = VimSign.SIGN_BREAKPOINT_RESOLVED if is_resolved else VimSign.SIGN_BREAKPOINT_UNRESOLVED
    super(BreakpointSign, self).__init__(vifx, name, bufnr, line_number)

class PCSign(VimSign):
  def __init__(self, vifx, bufnr, line_number, is_selected_thread):
    super(PCSign, self).__init__(vifx, VimSign.SIGN_PC, bufnr, line_number)
