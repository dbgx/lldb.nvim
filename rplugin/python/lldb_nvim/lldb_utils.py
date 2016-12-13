from __future__ import (absolute_import, division, print_function)

import os.path

__metaclass__ = type  # pylint: disable=invalid-name


def settings_target_source_map(commander):
    (success, output) = commander('settings show target.source-map')
    if not success:
        return None

    path_map = {}
    for line in output.splitlines()[1:]:
        try:
            path_src_start = line.index('"') + 1
            path_src, path_dest = line[path_src_start:-1].split('" -> "')
        except ValueError:
            continue
        if not os.path.isabs(path_src) or not os.path.isabs(path_dest):
            continue
        path_map[os.path.abspath(path_src)] = os.path.abspath(path_dest)

    return path_map


def resolve_line_entry(le, source_map=None):
    fullpath = le.file.fullpath
    if not source_map:
        return (fullpath, le.line)

    fullpath_new = None
    for path_src, path_dest in sorted(source_map.items(), key=lambda item: len(item[0])):
        if fullpath.startswith(path_src + os.path.sep):
            fullpath_new = path_dest + fullpath[len(path_src):]

    if fullpath_new is not None:
        fullpath = fullpath_new

    return (fullpath, le.line)


def get_pc_source_loc(thread, commander):
    """ Returns a tuple (thread_index, file, line) that represents where
        the PC sign should be placed for a thread.
    """
    frame = thread.GetSelectedFrame()
    frame_num = frame.GetFrameID()
    le = frame.GetLineEntry()
    while not le.IsValid() and frame_num < thread.GetNumFrames():
        frame_num += 1
        le = thread.GetFrameAtIndex(frame_num).line_entry

    if le.IsValid():
        return (thread.GetIndexID(),) + \
            resolve_line_entry(le, settings_target_source_map(commander))
    return None


def get_bploc_tuples(bp, source_map=None):
    """ Returns a list of tuples (file, line) where a breakpoint was resolved. """
    if not bp.IsValid():
        return []
    locs = []
    for bploc in bp:
        le_tupl = resolve_line_entry(bploc.GetAddress().line_entry, source_map)
        if le_tupl[0] and le_tupl[1] > 0:  # le_tupl[0] might be None
            locs.append(le_tupl)
    return locs


def get_description(lldb_obj):
    from lldb import SBStream
    s = SBStream()
    lldb_obj.GetDescription(s)
    return s.GetData()


def get_process_stat(target):
    from lldb import eStateStopped
    (proc, stat) = (None, '')
    if not target or not target.IsValid():
        stat = 'Target does not exist.'
    else:
        proc = target.GetProcess()
        if not proc or not proc.IsValid():
            proc = None
            stat = 'Process does not exist.'
        elif proc.GetState() == eStateStopped:
            pass
        else:
            stat = get_description(proc)
            exit_status = proc.GetExitStatus()
            if exit_status != -1:
                stat += ', exit status = %d' % exit_status
    return (proc, stat)
