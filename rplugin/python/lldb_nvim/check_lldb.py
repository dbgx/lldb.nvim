# Locate and load the lldb python module

from __future__ import (absolute_import, division, print_function)

import os
import sys

__metaclass__ = type  # pylint: disable=invalid-name


def probe():  # pylint: disable=too-many-branches
    """ Find and import the lldb modules. This function tries to find the lldb module by:
        1. Simply by doing "import lldb" in case the system python installation is aware of lldb.
           If that fails,
        2. Executes the lldb executable pointed to by the LLDB environment variable (or if unset,
           the first lldb on PATH") with the -P flag to determine the PYTHONPATH to set. If the
           lldb executable returns a valid path, it's added to sys.path and the import is attempted
           again. If that fails, 3. On Mac OS X the default Xcode 4.5 installation path.
    """

    # Try simple 'import lldb', in case of a system-wide install or a pre-configured PYTHONPATH
    try:
        import lldb  # pylint: disable=unused-variable
        return True
    except ImportError:
        pass

    # Allow overriding default path to lldb executable with the LLDB environment variable
    lldb_executable = 'lldb'
    if 'LLDB' in os.environ and os.path.exists(os.environ['LLDB']):
        lldb_executable = os.environ['LLDB']

    # Try using builtin module location support ('lldb -P')
    from subprocess import check_output, CalledProcessError
    try:
        with open(os.devnull, 'w') as fnull:
            lldb_minus_p_path = check_output(
                "%s -P" % lldb_executable, shell=True, stderr=fnull).strip()
        if not os.path.exists(lldb_minus_p_path):
            # lldb -P returned invalid path, probably too old
            pass
        else:
            sys.path.append(lldb_minus_p_path)
            import lldb  # NOQA
            return True
    except CalledProcessError:
        # Cannot run 'lldb -P' to determine location of lldb python module
        pass
    except ImportError:
        # Unable to import lldb module from path returned by `lldb -P`
        pass

    # On Mac OS X, try the default paths to XCode lldb module
    if "darwin" in sys.platform:
        xcode_python_path_base = '/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework'
        xcode_python_path = xcode_python_path_base + '/Versions/Current/Resources/Python/'
        if not os.path.exists(xcode_python_path):
            xcode_python_path = xcode_python_path_base + '/Resources/Python/'
        sys.path.append(xcode_python_path)
        try:
            import lldb  # NOQA
            return True
        except ImportError:
            # Unable to import lldb module from default Xcode python path
            pass

    return False
