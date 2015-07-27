from Queue import Queue

class VimX:
  def __init__(self, vim):
    self._vim = vim

  def eval(self, expr):
    vim = self._vim
    out_q = Queue()
    vim.session.threadsafe_call(lambda: out_q.put(vim.eval(expr)))
    return out_q.get()

  def command(self, cmd):
    vim = self._vim
    vim.session.threadsafe_call(lambda: vim.command(cmd))

  def log(self, msg, level=1):
    """ Execute echom in vim using appropriate highlighting. """
    level_map = ['None', 'WarningMsg', 'ErrorMsg']
    msg = msg.strip().replace('"', '\\"').replace('\n', '\\n')
    self.command('echohl %s | echom "%s" | echohl None' % (level_map[level], msg))

  def buffer_add(self, name):
    """ Create a buffer (if it doesn't exist) and return its number. """
    bufnr = self.eval('bufnr("%s", 1)' % name)
    self.command('call setbufvar(%d, "&bl", 1)' % bufnr)
    return bufnr

  def sign_jump(self, bufnr, sign_id):
    """ Try jumping to the specified sign_id in buffer with number bufnr. """
    self.command("call lldb#util#signjump(%d, %d)" % (bufnr, sign_id))

  def sign_place(self, sign_id, name, bufnr, line):
    """ Place a sign at the specified location. """
    cmd = "sign place %d name=%s line=%d buffer=%s" % (sign_id, name, line, bufnr)
    self.command(cmd)

  def sign_unplace(self, sign_id):
    """ Hide a sign with specified id. """
    self.command("sign unplace %d" % sign_id)

  def map_buffers(self, fn):
    """ Does a map using fn callback on all buffer object and returns a list.
        @param fn: callback function which takes buffer object as a parameter.
                   If None is returned, the item is ignored.
                   If a StopIteration is raised, the loop breaks.
        @return: The last item in the list returned is a placeholder indicating:
                 * completed iteration, if None is present
                 * otherwise, if StopIteration was raised, the message would be the last item
    """
    vim = self._vim
    out_q = Queue(maxsize=1)
    def map_buffers_inner():
      mapped = []
      breaked = False
      for b in vim.buffers:
        try:
          ret = fn(b)
          if ret is not None:
            mapped.append(ret)
        except StopIteration as e:
          mapped.append(e.message)
          breaked = True
          break
      if not breaked:
        mapped.append(None)
      out_q.put(mapped)
    vim.session.threadsafe_call(map_buffers_inner)
    return out_q.get()

  def get_buffer_name(self, nr):
    """ Get the buffer name given its number. """
    def name_mapper(b):
      if b.number == nr:
        raise StopIteration(b.name)
    return self.map_buffers(name_mapper)[0]

  def init_buffers(self):
    """ Create all lldb buffers and initialize the buffer map. """
    buf_map = self.eval('lldb#layout#init_buffers()')
    return buf_map
