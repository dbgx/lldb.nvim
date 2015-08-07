from collections import OrderedDict

class Session:
  def __init__(self, ctrl, vimx):
    self.ctrl = ctrl
    self.vimx = vimx
    self.state = OrderedDict()
    self.internal = {}

  def switch_mode(self, new_mode):
    if 'modes' not in self.state or new_mode not in self.state['modes']:
      self.vimx.log("Invalid mode!")
      return
    if '@mode' in self.internal:
      pass # TODO teardown
    if 'setup' in self.state['modes']:
      for action in self.state['modes']['setup']:
        pass # TODO setup
    self.internal['@mode'] = new_mode
    self.vimx.command('call lldb#layout#switch_mode("%s")' % new_mode)

  def handle(self, cmd, *args):
    from os import path

    if cmd == 'new':
      ret = self.vimx.call("lldb#session#new", len(self.state))
      if not (ret and '_file' in ret and '_file_bak' in ret):
        # FIXME accept blank _file or _file_bak?
        self.vimx.log("Skipped -- no session was created!")
        return
      head, tail = path.split(path.abspath(ret["_file"]))

      self.internal["@dir"] = head
      self.internal["@file"] = tail
      self.internal["@file_bak"] = ret['_file_bak'].format(**{'@file': tail})

      self.state["variables"] = OrderedDict()
      self.state["modes"] = OrderedDict([
          ("code", { }),
          ("debug", {
            "setup": [ "{@bp-set}", ],
            "teardown": [ "{@bp-save}" ]
          })
        ])

      if 'target' in ret and len(ret['target']):
        self.state["variables"]["target"] = ret["target"]
        debug = self.state["modes"]["debug"]
        debug["setup"].insert(0, "target create {target}")
        debug["setup"].append("process launch --stop-at-entry")
        debug["teardown"].append("target delete")

      self.state["breakpoints"] = []
      self.switch_mode('code')

    elif cmd == 'load' or cmd == 'save':
      if len(args) == 0:
        path = self.vimx.eval('findfile(g:lldb#session#file, ".;")')
      elif len(args) == 1:
        path = args[0]
      else:
        self.vimx.log("Too many arguments!")
        return

      if cmd == 'load':
        # TODO load(fp, object_pairs_hook=OrderedDict)
        self.vimx.log("Load %s" % path)
      else:
        self.vimx.log("Save to %s" % path)

    elif cmd == 'mode':
      if not len(args) == 1:
        self.vimx.log("Invalide number of arguments!")
        return
      self.switch_mode(args[0])

    elif cmd == 'show':
      if len(self.state) and len(self.internal) and self.internal['@file']:
        import json
        file_path = path.join(self.internal['@dir'], self.internal['@file'])
        sfile_bufnr = self.vimx.buffer_add(file_path)
        def json_show(b):
          if b.number == sfile_bufnr:
            b[:] = json.dumps(self.state, indent=4,
                              separators=(',', ': ')).split('\n')
            raise StopIteration
        self.vimx.command('exe "drop ".escape(bufname({0}), "$%# ")'.format(sfile_bufnr))
        self.vimx.map_buffers(json_show)

    else:
      self.vimx.log("Invalid sub-command: %s" % cmd)
