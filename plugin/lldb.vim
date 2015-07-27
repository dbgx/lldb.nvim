" ---------------------------------------------------------------------
"  File:        lldb.vim
"  Maintainer:  John C F <john.ch.fr@gmail.com>
"  --------------------------------------------------------------------

if (exists('g:loaded_lldb') && g:loaded_lldb) || !has('nvim') || !has('python')
  finish
endif
let g:loaded_lldb = 1

let g:lldb#_buffers = [ 'backtrace', 'breakpoints', 'disassembly', 'locals', 'registers', 'threads' ]

if !exists('g:lldb#layout#windows')
  let g:lldb#layout#windows = g:lldb#_buffers
endif
if !exists('g:lldb#layout#cmds')
  let g:lldb#layout#cmds = '.TRBBRkRkR'
endif

command! LLredraw call lldb#layout#teardown() | call lldb#layout#update()

highlight LLSelectedPCLine ctermbg=darkblue guibg=darkblue
highlight LLUnselectedPCLine ctermbg=black guibg=black
sign define llsign_bpres text=B>
sign define llsign_bpunres text=b>
sign define llsign_pcsel text=-> linehl=LLSelectedPCLine texthl=LLSelectedPCLine
sign define llsign_pcunsel text=-> linehl=LLUnselectedPCLine texthl=LLUnselectedPCLine
