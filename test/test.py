import sys
import os
import logging

logger = logging.getLogger(__name__)
logfile = ('test.log')
handler = logging.FileHandler(logfile, 'w')
handler.formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s @ '
    '%(filename)s:%(funcName)s:%(lineno)s] %(process)s - %(message)s')
logging.root.addHandler(handler)
logger.setLevel(logging.INFO)

NV_SOCK = 'NVIM_LISTEN_ADDRESS' #'LLTEST_SOCK'
if NV_SOCK not in os.environ:
  print '$%s not set!' % NV_SOCK
  exit(1)

import neovim
vim = neovim.attach('socket', path=os.environ[NV_SOCK])
vim.command('leftabove vsp ab.c')

plugpath = os.path.realpath('../rplugin/python')
sys.path.append(plugpath)

try:
  from lldb_nvim import Middleman
  iface = Middleman(vim)

  from time import sleep
  delay = 1
  iface._session(['load', 'lldb-nvim.json'])
  sleep(delay)
  iface._mode('debug')
  sleep(2*delay)
  iface._exec('continue')
  sleep(delay)
  iface._stdin('4\n')
  sleep(delay)
  iface._exec('continue')
  sleep(delay)
  iface._mode('code')
  iface._exit() # Don't forget to exit!
except:
  import traceback
  traceback.print_exc()

print ('Debugger terminated! If you see no errors, everything\'s cool!')
vim.command("wincmd w")
vim.command("belowright sp test.log")
