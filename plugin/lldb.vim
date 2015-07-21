" ---------------------------------------------------------------------
"  File:        lldb.vim
"  Maintainer:  John C F <john.ch.fr@gmail.com>
"  --------------------------------------------------------------------

if (exists('g:loaded_lldb') && g:loaded_lldb) || !has('nvim') || !has('python')
  finish
endif
let g:loaded_lldb = 1

let s:buffer_map = {}
let s:buffers = [ 'backtrace', 'breakpoints', 'disassembly', 'locals', 'registers', 'threads' ]
function! LLBuffersInit()
  let u_bnr = bufnr('%')
  for bname in s:buffers
    let bnr = bufnr(bname, 1)  " FIXME: add a unique prefix/suffix?
    call setbufvar(bnr, '&bt', 'nofile')
    call setbufvar(bnr, '&swf', 0)
    call setbufvar(bnr, '&ma', 0)
    exe 'silent b ' . bnr
    call setbufvar(bnr, '&nu', 0)
    call setbufvar(bnr, '&rnu', 0)
    let s:buffer_map[bname] = bnr
  endfor
  exe 'b ' . u_bnr
  return s:buffer_map
endfun

" takes one optional argument to specify whether to delete buffers
function! LLTabCheckClose(...)
  if empty(s:buffer_map)
    return
  endif
  let tabcount = 0
  for i in range(len(g:lldb_layout_cmds))
    if g:lldb_layout_cmds[i] == 'T'
      let tabcount += 1
    endif
  endfor
  if tabcount < tabpagenr('$')
    for i in range(tabcount)
      let tabnr = tabcount - i
      for bufnr in tabpagebuflist(tabnr)
        if index(g:lldb_layout_windows, bufname(bufnr)) >= 0
          exe 'tabclose ' . tabnr
          break
        endif
      endfor
    endfor
  else
    echom 'Please close unwanted tab(s) manually...'
  endif
  if a:0 == 0 || (a:0 > 0 && !a:1)
    return
  endif
  for bname in s:buffers
    let bnr = s:buffer_map[bname]
    exe 'silent bd ' . s:buffer_map[bname]
    call setbufvar(bnr, '&bt', 'nofile')
  endfor
  let s:buffer_map = {}
endfun

if !exists('g:lldb_layout_windows')
  let g:lldb_layout_windows = s:buffers
endif
if !exists('g:lldb_layout_cmds')
  let g:lldb_layout_cmds = '.TRBBRkRkR'
endif
function! LLUpdateLayout()
  if empty(s:buffer_map)
    call LLBuffersInit()
  endif
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

function! LLTrySignJump(bufnr, signid)
  if bufwinnr(a:bufnr) < 0
    let wnr = -1
    for i in range(winnr('$'))
      if index(values(s:buffer_map), winbufnr(i+1)) < 0
        let wnr = i+1
        break
      endif
    endfor
    if wnr < 0
      return
    endif
    exe wnr . "wincmd w"
    exe a:bufnr . 'b'
  endif
  exe 'sign jump ' . a:signid . ' buffer=' . a:bufnr
endfun

" Shamelessly copy/pasted from neovim/contrib/neovim_gdb/neovim_gdb.vim
function! LLGetExpression()
  let [lnum1, col1] = getpos("'<")[1:2]
  let [lnum2, col2] = getpos("'>")[1:2]
  let lines = getline(lnum1, lnum2)
  let lines[-1] = lines[-1][:col2 - 1]
  let lines[0] = lines[0][col1 - 1:]
  return join(lines, "\n")
endfun

command! LLredraw call LLTabCheckClose() | call LLUpdateLayout()

nnoremap <M-b> :call LLBreakswitch(bufnr('%'), getcurpos()[1])<CR>
nnoremap <S-F5> :LLredraw<CR>
nnoremap <F8> :LLcontinue<CR>
nnoremap <F9> :LLprint <C-R>=expand('<cword>')<CR>
nnoremap <S-F9> :LLpo <C-R>=expand('<cword>')<CR>
vnoremap <F9> :<C-U>LLprint <C-R>=LLGetExpression()<CR>
vnoremap <S-F9> :<C-U>LLpo <C-R>=LLGetExpression()<CR>

highlight LLSelectedPCLine ctermbg=darkblue guibg=darkblue
highlight LLUnselectedPCLine ctermbg=black guibg=black
sign define llsign_bpres text=B>
sign define llsign_bpunres text=b>
sign define llsign_pcsel text=-> linehl=LLSelectedPCLine texthl=LLSelectedPCLine
sign define llsign_pcunsel text=-> linehl=LLUnselectedPCLine texthl=LLUnselectedPCLine
