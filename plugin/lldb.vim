" ---------------------------------------------------------------------
"  File:        lldb.vim
"  Description: LLDB Debugger Integration Plugin
"  Maintainer:  Tobias Pflug <tobias.pflug@gmail.com>
"  License:     Same License as Vim itself
"  --------------------------------------------------------------------

if (exists('g:loaded_lldb') && g:loaded_lldb) || !has('nvim') || !has('python')
    finish
endif
let g:loaded_lldb = 1

let g:lldb_layout_order = [ 'breakpoints', 'backtrace', 'locals', 'threads', 'registers', 'disassembly' ]
let g:lldb_layout_cmds = 'VSSVjVjV'  " TODO: use A B L R instead of S V; use T0 for new tab at 0
let s:buffer_map = {}

function! s:NewBuffer(name, method)
  exe 'silent ' . a:method . ' ' . a:name
  setlocal bt=nofile noswf nonu nornu noma
  let s:buffer_map[a:name] = bufnr('%')
endfun

function! s:LoadBuffer(nr, method)
  let name = bufname(a:nr)
  exe 'silent ' . a:method . ' ' . name
endfun

function! LLUpdateLayout()
  tab sp
  tabmove 0

  let c = g:lldb_layout_cmds
  let o = g:lldb_layout_order
  let w = 0
  let is_first = len(s:buffer_map) == 0
  for i in range(len(c))
    if c[i] == 'V'
      if is_first
        call s:NewBuffer(o[w], 'vnew')
      else
        call s:LoadBuffer(o[w], 'vsp')
      endif
      let w += 1
    elseif c[i] == 'S'
      if is_first
        call s:NewBuffer(o[w], 'new')
      else
        call s:LoadBuffer(o[w], 'sp')
      endif
      let w += 1
    elseif c[i] == '-'
      if is_first
        call s:NewBuffer(o[w], 'e')
        b #
      endif
      let w += 1
    elseif c[i] == 'h' || c[i] == 'j' || c[i] == 'k' || c[i] == 'l'
      exe "normal \<c-w>" . c[i]
    endif
  endfor
  " TODO: make layout map { 'bufname': [tabnr, winnr] ... }
  return s:buffer_map
endfun

" Returns cword if search term is empty
function! LLCursorWord(term)
  return empty(a:term) ? expand('<cword>') : a:term
endfun

" Returns cleaned cWORD if search term is empty
function! LLCursorWORD(term)
  " Will strip all non-alphabetic characters from both sides
  return empty(a:term) ?  substitute(expand('<cWORD>'), '^\A*\(.\{-}\)\A*$', '\1', '') : a:term
endfun

" The parameters may have to be edited
noremap <C-B> :call LLBreakswitch('<C-R>=expand('%')<CR>', <C-R>=getcurpos()[1]<CR>)
"noremap <C-B> :call LLBreakswitch(expand('%'), getcurpos()[1])<CR>
