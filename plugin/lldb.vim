" ---------------------------------------------------------------------
"  File:        lldb.vim
"  Maintainer:  John C F <john.ch.fr@gmail.com>
"  --------------------------------------------------------------------

if exists('g:loaded_lldb') || !has('nvim') || !has('python')
  finish
endif
let g:loaded_lldb = 1

if !exists('g:lldb#session#file')
  let g:lldb#session#file = 'lldb-nvim.json'
endif
if !exists('g:lldb#session#backup_file_pat')
  let g:lldb#session#backup_file_pat = '.{0}.bak'
endif

command! LLredraw call lldb#layout#teardown() | call lldb#layout#setup()

highlight LLSelectedPCLine ctermbg=darkblue guibg=darkblue
highlight LLUnselectedPCLine ctermbg=black guibg=black
sign define llsign_bpres text=B>
sign define llsign_bpunres text=b>
sign define llsign_pcsel text=-> linehl=LLSelectedPCLine texthl=LLSelectedPCLine
sign define llsign_pcunsel text=-> linehl=LLUnselectedPCLine texthl=LLUnselectedPCLine
