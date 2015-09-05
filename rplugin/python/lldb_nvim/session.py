from collections import OrderedDict
from time import sleep
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
    self.help_flags = { "new": False,
                        "launch_prompt": True,
                        "session_show": True }

  def format(self, s):
    return s.format(**self.state['variables'])

  def run_actions(self, actions):
    from os import path
    lled = False

    self.ctrl.busy_more()
    for action in actions:
      if isinstance(action, basestring):
        typ, val = 'll', action
      else:
        typ, val = action

      if typ == 'sh':
        pass # TODO
      elif typ == 'bp':
        if val == 'set':
          for key, vals in self.state['breakpoints'].items():
            if key == "@ll":
              for cmd in vals:
                self.ctrl.exec_command(self.format(cmd))
            else:
              p = key if key[0] == '/' else path.join(self.internal['@dir'], key)
              for l in vals:
                self.ctrl.exec_command('breakpoint set -f %s -l %d' % (p, l))
          lled = True
        elif val == 'save':
          pass # TODO
      elif typ == 'll':
        self.ctrl.exec_command(self.format(val))
        lled = True
    self.ctrl.busy_less()

  def mode_setup(self, mode):
    if 'modes' not in self.state or mode not in self.state['modes']:
      self.vimx.log("Invalid mode!")
      return
    self.mode_teardown()
    if 'setup' in self.state['modes'][mode]:
      self.run_actions(self.state['modes'][mode]['setup'])
    self.internal['@mode'] = mode
    self.vimx.command("call call(g:lldb#session#mode_setup, ['%s'])" % mode)
    self.ctrl.update_buffers()
    if  self.help_flags["new"] and \
        self.help_flags["launch_prompt"] and \
        self.internal['@mode'] == 'debug':
      sleep(0.4)
      if self.ctrl.eval("input('Launch the target? [y/n] ', 'y')") == 'y':
        self.state['modes']['debug']['setup'].append('process launch')
        self.ctrl.exec_command('process launch')
        self.vimx.log('Process launched! Try `:LLsession show`', 0)
      self.help_flags["launch_prompt"] = False

  def mode_teardown(self):
    if '@mode' in self.internal:
      mode = self.internal['@mode']
      if 'teardown' in self.state['modes'][mode]:
        self.run_actions(self.state['modes'][mode]['teardown'])
      self.vimx.command("call call(g:lldb#session#mode_teardown, ['%s'])" % mode)
      del self.internal['@mode']
      return True
    return False

  def get_confpath(self):
    if '@file' in self.internal:
      from os import path
      return path.join(self.internal["@dir"], self.internal["@file"])
    else:
      return None

  def set_internal(self, confpath):
    from os import path
    head, tail = path.split(path.abspath(confpath))
    if len(head) == 0:
      return False
    self.internal["@dir"] = head
    self.internal["@file"] = tail
    return True

  def parse_and_load(self, conf_str):
    # TODO if there is a nice toml encoder available, add support for it
    state = self.json_decoder.decode(conf_str)
    if not isinstance(state, dict):
      raise ValueError("The root object must be an associative array")

    for key in ["variables", "modes", "breakpoints"]:
      if key not in state:
        state[key] = {}

    for key in state.keys():
      if key == "variables":
        pass # TODO check validity
      elif key == "modes":
        if len(state["modes"]) == 0:
          raise ValueError("At least one mode has to be defined")
      elif key == "breakpoints":
        pass
      else:
        raise ValueError("Invalid key '%s'" % key)

      if not isinstance(state[key], dict):
        raise ValueError('"%s" must be an associative array' % key)

    if self.mode_teardown():
      pass # TODO confirm whether to discard session
    self.state = state
    if len(self.state["modes"].keys()) > 0:
      self.mode_setup(self.state["modes"].keys()[0])

  def handle(self, cmd, *args):
    if cmd == 'new':
      ret = self.vimx.call("lldb#session#new", len(self.state))
      if not ret or '_file' not in ret or not self.set_internal(ret["_file"]):
        self.vimx.log("Skipped -- no session was created!")
        return

      try:
        self.parse_and_load("""
          { "variables": {},
            "modes": {
              "code": {},
              "debug": {
                "setup": [ ["bp", "set"] ],
                "teardown": [ ["bp", "save"] ]
              }
            },
            "breakpoints": {
              "@ll": ["breakpoint set -n main"]
            }
          }""")
      except ValueError as e:
        self.vimx.log("Unexpected error: " + str(e))
        return

      if 'target' in ret and len(ret['target']):
        self.state["variables"]["target"] = ret["target"]
        debug = self.state["modes"]["debug"]
        debug["setup"].insert(0, "target create {target}")
        debug["teardown"].append("target delete")
        self.help_flags["new"] = True

      self.mode_setup('code')

    elif cmd in ['load', 'reload']:
      if cmd == 'reload':
        if '@file' not in self.internal:
          self.vimx.log("No active session!")
          return
        if len(args) > 0:
          self.vimx.log("Too many arguments!")
          return
        confpath = self.get_confpath()
      elif len(args) == 0:
        confpath = self.vimx.eval('findfile(g:lldb#session#file, ".;")')
      elif len(args) == 1:
        confpath = args[0]
      else:
        self.vimx.log("Too many arguments!")
        return

      try:
        with open(confpath) as f:
          self.parse_and_load(''.join(f.readlines()))
      except (ValueError, IOError) as e:
        self.vimx.log("Bad session file: " + str(e))
        return
      self.set_internal(confpath)
      self.vimx.log("Loaded %s" % confpath)

    elif cmd == 'show':
      if len(self.state) and len(self.internal) and self.internal['@file']:
        from os import path
        import re
        file_path = path.join(self.internal['@dir'], self.internal['@file'])
        sfile_bufnr = self.vimx.buffer_add(file_path)
        json_str = json.dumps(self.state, indent=4, separators=(',', ': '))
        json_str = re.sub(r'\[\s*"(bp|ll|sh)",\s*"([^"]*)"\s*\]', r'[ "\1", "\2" ]', json_str)
        json_str = re.sub(r'(\[|[0-9]+,?)\s*(?=\]|[0-9]+)', r'\1 ', json_str)
        def json_show(b):
          if b.number == sfile_bufnr:
            b[:] = json_str.split('\n')
            raise StopIteration
        self.vimx.command('exe "tab drop ".escape(bufname({0}), "$%# ")'
                          .format(sfile_bufnr))
        self.vimx.map_buffers(json_show)
        if self.help_flags["new"] and self.help_flags["session_show"]:
          self.vimx.log('Save this file, and do `:LLsession reload` to load any manual changes made.')
          self.help_flags["session_show"] = False

    else:
      self.vimx.log("Invalid sub-command: %s" % cmd)
