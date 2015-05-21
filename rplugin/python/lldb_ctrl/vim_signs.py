
# Classes responsible for drawing signs in the Vim user interface.

class VimSign(object):
  SIGN_TEXT_BREAKPOINT_RESOLVED = "B>"
  SIGN_TEXT_BREAKPOINT_UNRESOLVED = "b>"
  SIGN_TEXT_PC = "->"
  SIGN_HIGHLIGHT_COLOUR_PC = 'darkblue'

  # unique sign id (for ':[sign/highlight] define)
  sign_id = 1

  # unique name id (for ':sign place')
  name_id = 1

  # Map of {(sign_text, highlight_colour) --> sign_name}
  defined_signs = {}

  def __init__(self, vim, sign_text, bufnr, line_number, highlight_colour=None):
    """ Define the sign and highlight (if applicable) and show the sign. """
    self.vim = vim

    # Get the sign name, either by defining it, or looking it up in the map of defined signs
    key = (sign_text, highlight_colour)
    if not key in VimSign.defined_signs:
      name = self.define(sign_text, highlight_colour)
    else:
      name = VimSign.defined_signs[key]

    self.show(name, bufnr, line_number)

  def define(self, sign_text, highlight_colour):
    """ Defines sign and highlight (if highlight_colour is not None). """
    sign_name = "sign%d" % VimSign.name_id
    if highlight_colour is None:
      self.vim.command("sign define %s text=%s" % (sign_name, sign_text))
    else:
      self.highlight_name = "highlight%d" % VimSign.name_id
      self.vim.command("highlight %s ctermbg=%s guibg=%s" %
          (self.highlight_name, highlight_colour, highlight_colour))
      self.vim.command("sign define %s text=%s linehl=%s texthl=%s" %
          (sign_name, sign_text, self.highlight_name, self.highlight_name))
    VimSign.defined_signs[(sign_text, highlight_colour)] = sign_name
    VimSign.name_id += 1
    return sign_name

  def show(self, name, bufnr, line_number):
    self.id = VimSign.sign_id
    VimSign.sign_id += 1
    self.vim.command("sign place %d name=%s line=%d buffer=%s" %
        (self.id, name, line_number, bufnr))

  def hide(self):
    self.vim.command("sign unplace %d" % self.id)

class BreakpointSign(VimSign):
  def __init__(self, vim, bufnr, line_number, is_resolved):
    txt = VimSign.SIGN_TEXT_BREAKPOINT_RESOLVED if is_resolved else VimSign.SIGN_TEXT_BREAKPOINT_UNRESOLVED
    super(BreakpointSign, self).__init__(vim, txt, bufnr, line_number)

class PCSign(VimSign):
  def __init__(self, vim, bufnr, line_number, is_selected_thread):
    super(PCSign, self).__init__(vim, VimSign.SIGN_TEXT_PC, bufnr, line_number,
                                 VimSign.SIGN_HIGHLIGHT_COLOUR_PC
                                     if is_selected_thread else None)
