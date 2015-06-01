import sys
import os

plugpath = os.path.realpath('../rplugin/python')
sys.path.append(plugpath)
from lldb_ctrl import LLInterface

NV_SOCK = 'NVIM_LISTEN_ADDRESS'
if NV_SOCK not in os.environ:
  print '$%s not set!' % NV_SOCK
  exit(1)

import neovim
vim = neovim.attach('socket', path=os.environ[NV_SOCK])
iface = LLInterface(vim)

from time import sleep
delay = 1
vim.command('sp ab.c')
bufnr = vim.eval('bufnr("ab.c")')
iface._target(['create ab'])
sleep(delay)
vim.command('call LLUpdateLayout()')
sleep(delay)
iface._breakpoint(['set -n main'])
sleep(delay)
iface._breakswitch([bufnr, 19])
sleep(delay)
iface._breakswitch([bufnr, 23])
sleep(delay)
iface._process(['launch'])
sleep(delay)
iface._continue([])
sleep(delay)
iface._continue([])
sleep(delay)
iface._process(['interrupt'])
sleep(delay)
iface._up([])
iface._up([])
iface._print(['f'])
sleep(delay)
iface._up([])
sleep(delay)
iface._print(['cc'])
sleep(delay)
iface._continue([])
left = 4
while left > 0:
  vim.command('echo "%s second(s) left..."' % left)
  sleep(1)
  left -= 1
vim.command('echo ""')
iface._refresh()
sleep(delay)
iface._continue([])

finalmsg = ('-- End of test --\\n'
            'Make sure there were no errors in python console.\\n'
            'You can use the variable `iface` from the console for further testing.')
vim.command('echo "%s"' % finalmsg)
