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
if !exists('g:lldb#session#mode_setup')
  let g:lldb#session#mode_setup = 'lldb#layout#setup'
endif
if !exists('g:lldb#session#mode_teardown')
  let g:lldb#session#mode_teardown = 'lldb#layout#teardown'
endif

let s:bp_symbol = get(g:, 'lldb#sign#bp_symbol', 'B>')
let s:pc_symbol = get(g:, 'lldb#sign#pc_symbol', '->')

highlight LLSelectedPCLine ctermbg=darkblue guibg=darkblue
highlight LLUnselectedPCLine ctermbg=black guibg=black

execute 'sign define llsign_bpres text=' . s:bp_symbol
execute 'sign define llsign_pcsel text=' . s:pc_symbol .
    \ ' texthl=LLSelectedPCLine linehl=LLSelectedPCLine'
execute 'sign define llsign_pcunsel text=' . s:pc_symbol .
    \ ' texthl=LLUnselectedPCLine linehl=LLUnselectedPCLine'
