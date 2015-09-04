from collections import OrderedDict
import json

class Session:
  def __init__(self, ctrl, vimx):
    import logging
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.INFO)

    self.ctrl = ctrl
    self.vimx = vimx
    self.state = OrderedDict()
    self.internal = {}
    self.json_decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)

  def format(self, s):
    return s.format(**self.state['variables'])

  def act(self, actions):
    from os import path
    lled = False

    for action in actions:
      if isinstance(action, basestring):
        t, a = 'll', action
      else:
        t, a = action

      if t == 'sh':
        pass
      elif t == 'bp':
        if a == 'set':
          for key, vals in self.state['breakpoints'].items():
            if key == "@ll":
              for cmd in vals:
                self.ctrl.exec_command(self.format(cmd))
            else:
              p = key if key[0] == '/' else path.join(self.internal['@dir'], key)
              for l in vals:
                self.ctrl.exec_command('breakpoint set -f %s -l %d' % (p, l))
          lled = True
        elif a == 'save':
          pass
      elif t == 'll':
        self.ctrl.exec_command(self.format(a))
        lled = True

    if lled: # FIXME make this unnecessary
      self.ctrl.update_buffers(buf='!all')

  def switch_mode(self, new_mode):
    if 'modes' not in self.state or new_mode not in self.state['modes']:
      self.vimx.log("Invalid mode!")
      return
    self.ctrl.busy_more()
    if '@mode' in self.internal:
      mode = self.internal['@mode']
      if 'teardown' in self.state['modes'][mode]:
        self.act(self.state['modes'][mode]['teardown'])
    if 'setup' in self.state['modes'][new_mode]:
      self.act(self.state['modes'][new_mode]['setup'])
    self.internal['@mode'] = new_mode
    self.vimx.call('lldb#layout#switch_mode', new_mode, async=True)
    self.ctrl.busy_less()
    self.ctrl.update_buffers()

  def set_internal(self, confpath):
    from os import path
    head, tail = path.split(path.abspath(confpath))
    self.internal["@dir"] = head
    self.internal["@file"] = tail

  def handle(self, cmd, *args):
    if cmd == 'new':
      ret = self.vimx.call("lldb#session#new", len(self.state))
      if not ret or '_file' not in ret:
        # FIXME accept blank _file?
        self.vimx.log("Skipped -- no session was created!")
        return
      self.set_internal(ret["_file"])

      self.state = self.json_decoder.decode("""
        {
          "variables": {},
          "modes": {
            "code": {},
            "debug": {
              "setup": [
                ["bp", "set"]
              ],
              "teardown": [
                ["bp", "save"]
              ]
            }
          },
          "breakpoints": {
            "@ll": ["breakpoint set -n main"]
          }
        }""")

      if 'target' in ret and len(ret['target']):
        self.state["variables"]["target"] = ret["target"]
        debug = self.state["modes"]["debug"]
        debug["setup"].insert(0, "target create {target}")
        debug["setup"].append("process launch")
        debug["teardown"].append("target delete")

      self.switch_mode('code')

    elif cmd == 'load' or cmd == 'save':
      if len(args) == 0:
        confpath = self.vimx.eval('findfile(g:lldb#session#file, ".;")')
      elif len(args) == 1:
        confpath = args[0]
      else:
        self.vimx.log("Too many arguments!")
        return

      if cmd == 'load':
        with open(confpath) as f:
          self.state = self.json_decoder.decode(''.join(f.readlines()))
        # TODO check for validity
        # FIXME if a session is active, confirm whether to discard it
        self.set_internal(confpath)
        self.vimx.log("Loaded %s" % confpath)
      else:
        self.vimx.log("(Todo) Save to %s" % confpath)

    elif cmd == 'show':
      if len(self.state) and len(self.internal) and self.internal['@file']:
        from os import path
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
