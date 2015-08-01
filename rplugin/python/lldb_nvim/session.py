class Session:
  def __init__(self, vimx):
    self.vimx = vimx
    self.state = {}

  def handle(self, cmd, *args):
    if cmd == 'new':
      ret = self.vimx.eval("lldb#session#new(%d)" % len(self.state))
      # FIXME either or both could be blank
      self.state["_file"] = ret["_file"]
      self.state["_file_bak"] = ret['_bak_pat'].replace('{0}', ret["_file"])
      self.state["target"] = { "file": ret["target"], "more-opts": None }
      self.state["process"] = { "stdin": None, "stdout": None, "more-opts": None }
      self.state["breakpoints"] = []
    elif cmd == 'load' or cmd == 'save':
      if len(args) == 0:
        path = self.vimx.eval('findfile(g:lldb#session#file, ".;")')
      elif len(args) == 1:
        path = args[0]
      else:
        self.vimx.log("Too many arguments!")
        return

      if cmd == 'load':
        self.vimx.log("Load %s" % path)
      else:
        self.vimx.log("Save to %s" % path)
    elif cmd == 'show':
      if len(self.state) and self.state['_file']:
        import json
        state = self.state.copy()
        sfile_bufnr = self.vimx.buffer_add(state['_file'])
        del state['_file'], state['_file_bak']
        def json_show(b):
          if b.number == sfile_bufnr:
            b[:] = json.dumps(state, sort_keys=True,
                              indent=4, separators=(',', ': ')).split('\n')
            raise StopIteration
        self.vimx.command('exe "drop ".escape(bufname({0}), "$%# ")'.format(sfile_bufnr))
        self.vimx.map_buffers(json_show)
    else:
      self.vimx.log("Invalid sub-command: %s" % cmd)
