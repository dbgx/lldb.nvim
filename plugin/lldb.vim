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

let s:buffer_map = {}
let s:buffers = [ 'backtrace', 'breakpoints', 'disassembly', 'locals', 'registers', 'threads' ]
function! LLBuffersInit()
  for i in range(len(s:buffers))
    let bnr = bufnr(s:buffers[i], 1)  " FIXME: add a unique prefix/suffix?
    call setbufvar(bnr, '&bt', 'nofile')
    call setbufvar(bnr, '&ma', 0)
    call setbufvar(bnr, '&nu', 0)  " FIXME: may not work
    call setbufvar(bnr, '&rnu', 0)  " FIXME: may not work
    call setbufvar(bnr, '&swf', 0)
    let s:buffer_map[s:buffers[i]] = bnr
  endfor
  return s:buffer_map
endfun

if !exists('g:lldb_layout_windows')
  let g:lldb_layout_windows = s:buffers
endif
if !exists('g:lldb_layout_cmds')
  let g:lldb_layout_cmds = '.TRBBRkRkR'
endif
function! LLUpdateLayout()
  let code_buf = bufname('%')
  if index(s:buffers, code_buf) >= 0
    let code_buf = '[No Name]'
  endif
  let c = g:lldb_layout_cmds
  let w = g:lldb_layout_windows
  let ci = 0
  let wi = 0
  let tabi = 0
  while ci < len(c)
    if c[ci] == '.'
      " Next command should create a code window
      let bname = code_buf
      let ci += 1
    elseif stridx('TABLR', c[ci]) >= 0
      let bname = w[wi]
      let wi += 1
    endif
    if c[ci] == 'T'
      exe 'tab sp ' . bname
      exe 'tabmove ' tabi
      let tabi += 1
    elseif c[ci] == 'A'
      exe 'above sp ' . bname
    elseif c[ci] == 'B'
      exe 'below sp ' . bname
    elseif c[ci] == 'L'
      exe 'above vsp ' . bname
    elseif c[ci] == 'R'
      exe 'below vsp ' . bname
    elseif stridx('hjkl', c[ci]) >= 0
      exe "normal \<c-w>" . c[ci]
    endif
    let ci += 1
  endwhile
  return tabi
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
