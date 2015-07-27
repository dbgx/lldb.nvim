class Session:
  def __init__(self, vimx):
    self.vimx = vimx

  def handle(self, cmd, *args):
    self.vimx.log("Got sub-command: %s" % cmd)
