from __future__ import (absolute_import, division, print_function)

from collections import OrderedDict
from time import sleep
import json

__metaclass__ = type  # pylint: disable=invalid-name


class Session:  # pylint: disable=too-many-instance-attributes

    def __init__(self, ctrl, vimx):
        import logging
        self.logger = logging.getLogger(__name__)

        self.ctrl = ctrl
        self.vimx = vimx
        self.state = OrderedDict()
        self.internal = {}
        self.json_decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
        self.help_flags = {"new": False, "launch_prompt": True, "session_show": True}
        self.bpid_map = {}

    def isalive(self):
        """ Returns true if a well-defined session is alive """
        return len(self.state) > 1 and '@file' in self.internal and '@mode' in self.internal

    def bp_map_auto(self, bp, fallback=None):
        """ Sets the value of bp.id key by trying to resolve bp to a single location;
            if not possible, sets the value to fallback
        """
        from .lldb_utils import get_bploc_tuples, settings_target_source_map
        if bp.GetNumLocations() == 1:
            self.bpid_map[bp.id] = get_bploc_tuples(
                bp, settings_target_source_map(self.ctrl.get_command_result))[0]
        else:
            self.bpid_map[bp.id] = fallback

    def new_target(self, target):
        self.bpid_map = {}
        if target.GetNumBreakpoints() > 0:
            self.logger.warn("New target has breakpoints!")
            for bp in target.breakpoint_iter():  # patch up
                self.bp_map_auto(bp)

    def bp_changed(self, cmd, bp_iter):  # pylint: disable=too-many-branches
        import re
        old_bps = set(self.bpid_map.keys())
        cur_bps = set()
        bpid_llobj_map = {}
        for bp in bp_iter:
            cur_bps.add(bp.id)
            bpid_llobj_map[bp.id] = bp

        new_bps = cur_bps - old_bps
        del_bps = old_bps - cur_bps
        if len(new_bps) == 1:
            bpid = new_bps.pop()
            bp = bpid_llobj_map[bpid]
            if re.match(r'(b|tbreak|_regexp-t?break|) \S+:[0-9]+\s*$', cmd):
                self.bp_map_auto(bp, cmd)
            else:
                self.bpid_map[bpid] = cmd
        elif len(new_bps) > 1:  # from loading a script file?
            for bpid in new_bps:
                self.bpid_map[bpid] = None
            self.logger.warn("Multiple new breakpoints!")

        if len(del_bps) > 0:
            for bpid in del_bps:
                del self.bpid_map[bpid]
            self.logger.info("Deleted breakpoints %s!", repr(list(del_bps)))

    def bp_set(self):
        if self.ctrl.target is None:
            self.vimx.log("Setting breakpoints requires a target!")
            return
        for key, vals in self.state['breakpoints'].items():
            if key == "@ll":
                for cmd in vals:
                    self.ctrl.exec_command(self.format(cmd))
            else:
                for l in vals:
                    self.ctrl.bp_set_line(key, l)

    def bp_save(self):  # pylint: disable=too-many-branches
        file_bp_map = {"@ll": []}
        for bp_val in self.bpid_map.values():
            if isinstance(bp_val, basestring):
                file_bp_map["@ll"].append(bp_val)
            elif bp_val is not None:
                abspath, line = bp_val
                relpath = self.path_shorten(abspath)
                if relpath in file_bp_map:
                    file_bp_map[relpath].append(line)
                else:
                    file_bp_map[relpath] = [line]
        for key in file_bp_map:
            if key != "@ll":
                file_bp_map[key] = sorted(set(file_bp_map[key]))
        self.state['breakpoints'] = file_bp_map

    def format(self, s):
        return s.format(**self.state['variables'])

    def run_actions(self, actions):  # pylint: disable=too-many-branches
        self.ctrl.busy_more()
        for action in actions:
            if isinstance(action, basestring):
                typ, val = 'll', action
            else:
                typ, val = action

            if typ == 'sh':
                pass  # TODO
            elif typ == 'bp':
                if val == 'set':
                    self.bp_set()
                elif val == 'save':
                    self.bp_save()
            elif typ == 'll':
                self.ctrl.exec_command(self.format(val))
        self.ctrl.busy_less()

    def get_modes(self):
        if 'modes' in self.state:
            return self.state['modes'].keys()
        else:
            return []

    def mode_setup(self, mode):
        """ Tear down the current mode, and switch to a new one. """
        if mode not in self.get_modes():
            self.vimx.log("Invalid mode!")
            return
        self.mode_teardown()
        self.internal['@mode'] = mode
        self.vimx.command("call call(g:lldb#session#mode_setup, ['%s'])" % mode)
        if 'setup' in self.state['modes'][mode]:
            self.run_actions(self.state['modes'][mode]['setup'])
        self.ctrl.update_buffers()
        if self.help_flags["new"] and \
                self.help_flags["launch_prompt"] and \
                self.internal['@mode'] == 'debug':
            sleep(0.4)
            if self.vimx.eval("input('Launch the target? [y=yes] ', 'y')") == 'y':
                self.state['modes']['debug']['setup'].append('process launch')
                self.ctrl.exec_command('process launch')
                self.vimx.log('Process launched! Try `:LLsession show`', 0)
            self.help_flags["launch_prompt"] = False

    def mode_teardown(self):
        if self.isalive():
            mode = self.internal['@mode']
            if 'teardown' in self.state['modes'][mode]:
                self.run_actions(self.state['modes'][mode]['teardown'])
            self.vimx.command("call call(g:lldb#session#mode_teardown, ['%s'])" % mode)
            del self.internal['@mode']
            return True
        return False

    def get_confpath(self):
        if self.isalive():
            from os import path
            return path.join(self.internal["@dir"], self.internal["@file"])
        else:
            return None

    def path_from_vim(self, vpath):
        from os import path
        vim_cwd = self.vimx.eval("getcwd()")
        return path.join(vim_cwd, vpath)

    def path_shorten(self, abspath):
        from os import path
        return path.relpath(abspath, self.internal["@dir"])

    def set_path(self, confpath):
        from os import path, chdir
        head, tail = path.split(path.abspath(confpath))
        if len(tail) == 0:
            self.vimx.log("Error: invalid path!")
            return False
        try:
            chdir(head)
        except OSError as e:
            self.vimx.log("%s" % e)
            return False
        self.internal["@dir"] = head
        self.internal["@file"] = tail
        return True

    def parse_and_load(self, conf_str):  # pylint: disable=too-many-branches
        # TODO if there is a nice toml encoder available, add support for it
        state = self.json_decoder.decode(conf_str)
        if not isinstance(state, dict):
            raise ValueError("The root object must be an associative array")

        for key in ["variables", "modes", "breakpoints"]:
            if key not in state:
                state[key] = {}

        for key in state:
            if key == "variables":
                pass  # TODO check validity
            elif key == "modes":
                if len(state["modes"]) == 0:
                    raise ValueError("At least one mode has to be defined")
            elif key == "breakpoints":
                pass
            else:
                raise ValueError("Invalid key '%s'" % key)

            if not isinstance(state[key], dict):
                raise ValueError('"%s" must be an associative array' % key)

        self.mode_teardown()
        self.state = state
        self.mode_setup(self.state["modes"].keys()[0])

    def handle(self, cmd, *args):  # pylint: disable=too-many-return-statements,too-many-branches
        """ Handler for :LLsession commands. """
        if cmd == 'new':
            if self.isalive() and self.vimx.eval("lldb#session#discard_prompt()") == 0:
                self.vimx.log("Session left unchanged!", 0)
                return

            ret = self.vimx.eval("lldb#session#new()")
            if not ret or '_file' not in ret:
                self.vimx.log("Skipped -- no session was created!")
                return
            if not self.set_path(ret["_file"]):
                return

            try:
                self.parse_and_load("""{
                    "variables": {},
                    "modes": {
                        "code": {},
                        "debug": {
                            "setup": [["bp", "set"]],
                            "teardown": [["bp", "save"]]
                        }
                    },
                    "breakpoints": {
                        "@ll": ["breakpoint set -n main"]
                    }
                }""")
            except ValueError as e:
                self.vimx.log("Unexpected error: " + str(e))
                return

            if 'target' in ret and len(ret['target']) > 0:
                self.state["variables"]["target"] = \
                    self.path_shorten(self.path_from_vim(ret["target"]))
                debug = self.state["modes"]["debug"]
                debug["setup"].insert(0, "target create {target}")
                debug["teardown"].append("target delete")
                self.help_flags["new"] = True

            self.vimx.log("New session created!", 0)

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

            if self.isalive() and cmd == 'load' and \
                    self.vimx.eval("lldb#session#discard_prompt()") == 0:
                self.vimx.log("Session left unchanged!", 0)
                return

            try:
                with open(confpath) as f:
                    self.parse_and_load(''.join(f.readlines()))
            except (ValueError, IOError) as e:
                self.vimx.log("Bad session file: " + str(e))
            else:
                self.set_path(confpath)
                self.vimx.log("Loaded %s" % confpath, 0)

        elif cmd == 'show':
            if self.isalive():
                import re
                sfile_bufnr = self.vimx.buffer_add(self.get_confpath())
                self.vimx.command('exe "tab drop ".escape(bufname({0}), "$%# ")'
                                  .format(sfile_bufnr))

                json_str = json.dumps(self.state, indent=4, separators=(',', ': '))
                json_str = re.sub(r'\[\s*"(bp|ll|sh)",\s*"([^"]*)"\s*\]',
                                  r'[ "\1", "\2" ]', json_str)
                json_str = re.sub(r'(\[|[0-9]+,?)\s+(?=\]|[0-9]+)', r'\1 ', json_str)

                def json_show(b):
                    if b.number == sfile_bufnr:
                        b[:] = json_str.split('\n')
                        raise StopIteration

                self.vimx.map_buffers(json_show)
                if self.help_flags["new"] and self.help_flags["session_show"]:
                    self.vimx.log(
                        'Save this file, and do `:LLsession reload` to load any changes made.')
                    self.help_flags["session_show"] = False
            else:
                self.vimx.log("No active session.")

        elif cmd == 'bp-set' and self.isalive():
            self.bp_set()
        elif cmd == 'bp-save' and self.isalive():
            self.bp_save()

        else:
            self.vimx.log("Invalid sub-command: %s" % cmd)
