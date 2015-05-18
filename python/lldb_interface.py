
#
# This file defines the layer that talks to the debugger subprocess
#

class LLDBInterface(object):
  def __init__(self, pid):
    self.pid = pid
