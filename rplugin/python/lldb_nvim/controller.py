from __future__ import (absolute_import, division, print_function)

from threading import Thread
from Queue import Queue, Empty, Full

import lldb

from .vim_buffers import VimBuffers
from .session import Session

__metaclass__ = type  # pylint: disable=invalid-name


class EventLoopError(Exception):
    pass


class Controller(Thread):  # pylint: disable=too-many-instance-attributes
    """ Thread object that handles LLDB events and commands. """

    CTRL_VOICE = 238  # doesn't matter what this is
    TARG_NEW = 1
    TARG_DEL = 1 << 1
    PROC_NEW = 1 << 2
    PROC_DEL = 1 << 3
    BP_CHANGED = 1 << 4
    BAD_STATE = 1 << 5  # multiple targets

    def __init__(self, vimx):
        """ Creates the LLDB SBDebugger object and more! """
        import logging
        self.logger = logging.getLogger(__name__)

        self._sink = open('/dev/null')
        self._dbg = lldb.SBDebugger.Create()
        self._dbg.SetOutputFileHandle(self._sink, False)
        self._ipreter = self._dbg.GetCommandInterpreter()

        self._rcx = lldb.SBListener("the_ear")  # receiver
        self._trx = lldb.SBBroadcaster("the_mouth")  # transmitter for user events
        self._trx.AddListener(self._rcx, self.CTRL_VOICE)

        self.target = None
        self._process = None
        self._proc_cur_line_len = 0
        self._proc_lines_count = 0
        self._proc_sigstop_count = 0
        self._num_bps = 0

        self.in_queue = Queue(maxsize=2)
        self.out_queue = Queue(maxsize=1)

        self.vimx = vimx
        self.busy_stack = 0  # when > 0, buffers are not updated
        self.buffers = VimBuffers(self, vimx)
        self.session = Session(self, vimx)

        super(Controller, self).__init__()  # start the thread

    def is_busy(self):
        return self.busy_stack > 0

    def busy_more(self):
        self.busy_stack += 1

    def busy_less(self):
        self.busy_stack -= 1
        if self.busy_stack < 0:
            self.logger.critical("busy_stack < 0")
            self.busy_stack = 0

    def safe_call(self, method, args=None, sync=False, timeout=None):
        """ (thread-safe) Call `method` with `args`. If `sync` is True, wait for
            `method` to complete and return its value. If timeout is set and non-
            negative, and the `method` did not complete within `timeout` seconds,
            an EventLoopError is raised!
        """
        if self._dbg is None:
            self.logger.critical("Debugger not found!")
            raise EventLoopError("Dead debugger!")
        if self.out_queue.full():  # garbage
            self.out_queue.get()  # clean

        try:
            self.in_queue.put((method, args if args else [], sync), block=False)
            interrupt = lldb.SBEvent(self.CTRL_VOICE, "the_sound")
            self._trx.BroadcastEvent(interrupt)
            if sync:
                return self.out_queue.get(block=True, timeout=timeout)
        except Empty:
            raise EventLoopError("Timed out!")
        except Full:
            self.logger.critical("Event loop thread is probably dead!")
            raise EventLoopError("Dead event loop!")

    def safe_execute(self, tokens):
        """ (thread-safe) Executes an lldb command defined by a list of tokens.
            If a token contains white-spaces, they are escaped using backslash.
        """
        cmd = ' '.join([t.replace(' ', '\\ ') for t in tokens])
        self.safe_call(self.exec_command, [cmd])

    def safe_exit(self):
        """ Exit from the event-loop, and wait for the thread to join.
            Should be called from outside this thread.
        """
        self.safe_call(None)
        self.join()

    def complete_command(self, arg, line, pos):
        """ Returns a list of viable completions for line, and cursor at pos. """
        pos = int(pos)
        result = lldb.SBStringList()

        if arg == line and line != '':
            # provide all possible completions when completing 't', 'b', 'di' etc.
            self._ipreter.HandleCompletion('', 0, 1, -1, result)
            cands = ['']
            for x in result:
                if x == line:
                    cands.insert(1, x)
                elif x.startswith(line):
                    cands.append(x)
        else:
            self._ipreter.HandleCompletion(line, pos, 1, -1, result)
            cands = [x for x in result]

        if len(cands) > 1:
            if cands[0] == '' and arg != '':
                if not cands[1].startswith(arg) or not cands[-1].startswith(arg):
                    return []
            return cands[1:]
        else:
            return []

    def update_buffers(self, buf=None):
        """ Update lldb buffers and signs placed in source files.
            @param buf
                If None, all buffers and signs would be updated.
                Otherwise, update only the specified buffer.
        """
        if self.is_busy():
            return
        if buf is None:
            self.buffers.update(self.target)
        else:
            self.buffers.update_buffer(buf, self.target)

    def get_state_changes(self):  # pylint: disable=too-many-branches
        """ Get a value denoting how target, process, and/or breakpoint have changed.
            If a new process found, add our listener to its broadcaster.
        """
        changes = 0
        if self._dbg.GetNumTargets() > 1:
            return self.BAD_STATE

        if self.target is None or not self.target.IsValid():
            target = self._dbg.GetSelectedTarget()
            if target.IsValid():
                changes = self.TARG_NEW
                self.target = target
            elif self.target is not None:
                changes = self.TARG_DEL
                self.target = None

        if self.target is None:
            if self._process is not None:
                changes |= self.PROC_DEL
                self._process = None
            if self._num_bps > 0:
                changes |= self.BP_CHANGED
                self._num_bps = 0
            return changes

        if self._process is None or not self._process.IsValid():
            process = self.target.process
            if process.IsValid():
                changes |= self.PROC_NEW
                self._process = process
                process.broadcaster.AddListener(
                    self._rcx,
                    lldb.SBProcess.eBroadcastBitStateChanged |
                    lldb.SBProcess.eBroadcastBitSTDOUT |
                    lldb.SBProcess.eBroadcastBitSTDERR
                )
                self._proc_cur_line_len = 0
                self._proc_lines_count = 0
                self._proc_sigstop_count = 0

            elif self._process is not None:
                changes |= self.PROC_DEL
                self._process = None

        num_bps = self.target.GetNumBreakpoints()
        if self._num_bps != num_bps:
            # TODO what if one was added and another deleted?
            changes |= self.BP_CHANGED
            self._num_bps = num_bps
        # TODO Watchpoints

        return changes

    def change_buffer_cmd(self, buf, cmd):
        """ Change a buffer command and update it. """
        self.buffers.content_map[buf] = cmd
        self.update_buffers(buf=buf)
        if self.target is not None:
            self.vimx.command('drop [lldb]%s' % buf)

    def do_btswitch(self):
        """ Switch backtrace command to show all threads. """
        cmd = self.buffers.content_map['backtrace']
        if cmd != 'bt all':
            cmd = 'bt all'
        else:
            cmd = 'bt'
        self.change_buffer_cmd('backtrace', cmd)

    def bp_set_line(self, spath, line):
        from os.path import abspath
        fpath = abspath(spath).encode('ascii', 'ignore')
        bp = self.target.BreakpointCreateByLocation(fpath, line)
        self.buffers.logs_append(u'\u2192(lldb-bp) %s:%d\n' % (spath, line))
        self.session.bp_map_auto(bp, (spath, line))
        self.update_buffers(buf='breakpoints')

    def do_breakswitch(self, bufnr, line):
        """ Switch breakpoint at the specified line in the buffer. """
        key = (bufnr, line)
        if key in self.buffers.bp_list:
            bps = self.buffers.bp_list[key]
            args = "delete %s" % " ".join([str(b.GetID()) for b in bps])
            self.exec_command("breakpoint " + args)
        else:
            self.bp_set_line(self.vimx.get_buffer_name(bufnr), line)

    def do_breakdelete(self, bp_id):
        """ Delete a breakpoint by id """
        if bp_id:
            self.exec_command("breakpoint delete {}".format(bp_id))

    def put_stdin(self, instr):
        """ Call PutSTDIN() of process with instr. """
        if self._process is not None:
            self._process.PutSTDIN(instr)
        else:
            self.vimx.log('No active process!')

    def get_command_result(self, command, add2hist=False):
        """ Runs command in the interpreter and returns (success, output)
            Not to be called directly for commands which changes debugger state;
            use exec_command instead.
        """
        result = lldb.SBCommandReturnObject()
        cmd = command.encode('ascii', 'ignore')

        self._ipreter.HandleCommand(cmd, result, add2hist)

        self.logger.debug('(lldb) %s\n%s', cmd, result)

        return (result.Succeeded(),
                result.GetOutput() if result.Succeeded() else result.GetError())

    def exec_command(self, command):
        """ Runs command in the interpreter, calls update_buffers, and display the
            result in the logs buffer. Returns True if succeeded.
        """
        self.buffers.logs_append(u'\u2192(lldb) %s\n' % command)
        (success, output) = self.get_command_result(command, True)
        if not success:
            self.buffers.logs_append(output, u'\u2717')
        elif len(output) > 0:
            self.buffers.logs_append(output, u'\u2713')

        state_changes = self.get_state_changes()
        if state_changes & self.TARG_NEW != 0:
            self.session.new_target(self.target)
        elif state_changes & self.BP_CHANGED != 0 and self.target is not None:
            self.session.bp_changed(command, self.target.breakpoint_iter())

        self.update_buffers()
        return success

    def run(self):  # pylint: disable=too-many-branches,too-many-statements
        """ This thread's event loop. """
        import traceback
        to_count = 0
        while True:
            event = lldb.SBEvent()
            if self._rcx.WaitForEvent(30, event):  # 30 second timeout

                def event_matches(broadcaster, skip=True):
                    if event.BroadcasterMatchesRef(broadcaster):
                        if skip:
                            while self._rcx.GetNextEventForBroadcaster(broadcaster, event):
                                pass
                        return True
                    return False

                if event_matches(self._trx, skip=False):
                    try:
                        method, args, sync = self.in_queue.get(block=False)
                        if method is None:
                            break
                        self.logger.info('Calling %s with %s', method.func_name, repr(args))
                        ret = method(*args)
                        if sync:
                            self.out_queue.put(ret, block=False)
                    except Exception:  # pylint: disable=broad-except
                        self.logger.critical(traceback.format_exc())

                elif event_matches(self._process.broadcaster):
                    # Dump stdout and stderr to logs buffer
                    while True:
                        out = ''
                        stdout = self._process.GetSTDOUT(256)
                        if stdout is not None:
                            out += stdout
                        stderr = self._process.GetSTDERR(256)
                        if stderr is not None:
                            out += stderr
                        if len(out) == 0:
                            break
                        n_lines = self.buffers.logs_append(out)
                        if n_lines == 0:
                            self._proc_cur_line_len += len(out)
                        else:
                            self._proc_cur_line_len = 0
                            self._proc_lines_count += n_lines
                        if self._proc_cur_line_len > 8192 or self._proc_lines_count > 2048:
                            # detect and stop/kill insane process
                            if self._process.state == lldb.eStateStopped:
                                pass
                            elif self._proc_sigstop_count > 7:
                                self._process.Kill()
                                self.buffers.logs_append(
                                    u'\u2717SIGSTOP limit exceeded! Sent SIGKILL!\n')
                            else:
                                self._process.SendAsyncInterrupt()
                                self._proc_sigstop_count += 1
                                self.buffers.logs_append(
                                    u'\u2717Output limits exceeded! Sent SIGSTOP!\n')
                            break
                    # end of dump while
                    self.update_buffers()

            else:  # Timed out
                to_count += 1
                if to_count > 172800:  # in case WaitForEvent() does not wait!
                    self.logger.critical('Broke the loop barrier!')
                    break
        # end of event-loop while

        self._dbg.Terminate()
        self._dbg = None
        self._sink.close()
        self.logger.info('Terminated!')
