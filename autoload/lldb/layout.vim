function! s:logs_clear()
  if input('Clear logs [y=yes]? ') == 'y'
    if expand('%') == '[lldb]logs'
      set ma
      norm! ggdG
      set noma
    endif
  endif
endfun

function! lldb#layout#init_buffers()
  let s:buffers = [ 'backtrace', 'breakpoints', 'disassembly',
                  \ 'locals', 'logs', 'registers', 'threads' ]
  let s:buffer_map = {}
  let u_bnr = bufnr('%')
  for bname in s:buffers
    let bnr = bufnr('[lldb]' . bname, 1)
    call setbufvar(bnr, '&ft', 'lldb')
    call setbufvar(bnr, '&bt', 'nofile')
    call setbufvar(bnr, '&swf', 0)
    call setbufvar(bnr, '&ma', 0)
    exe 'silent b ' . bnr
    if bname == 'logs'
      nnoremap <buffer> i :call lldb#remote#stdin_prompt()<CR>
      nnoremap <silent> <buffer> <nowait> d :call <SID>logs_clear()<CR>
      nnoremap <silent> <buffer> <nowait> q :drop #<CR>
    endif
    call setbufvar(bnr, '&nu', 0)
    call setbufvar(bnr, '&rnu', 0)
    call setbufvar(bnr, '&bl', 0)
    let s:buffer_map[bname] = bnr
  endfor
  exe 'b ' . u_bnr
  return s:buffer_map
endfun

function! lldb#layout#setup(mode)
  if a:mode != 'debug'
    return
  endif
  if !exists('s:buffer_map') || empty(s:buffer_map)
    call lldb#layout#init_buffers()
  endif
  let code_buf = bufnr('%')
  if index(s:buffers, code_buf) >= 0
    let code_buf = '[No Name]'
  endif
  exe '0tab sb ' . code_buf
  let winw2 = winwidth(0)*2/5
  let winw3 = winwidth(0)*3/5
  let winh2 = winheight(0)*2/3
  exe 'belowright ' . winw3 . 'vsp +b' . s:buffer_map['threads']
  exe 'belowright ' . winh2 . 'sp +b' . s:buffer_map['disassembly']
  exe 'belowright ' . winw3/2 . 'vsp +b' . s:buffer_map['registers']
  exe '0tab sb ' . code_buf
  exe 'belowright ' . winw2 . 'vsp +b' . s:buffer_map['backtrace']
  exe 'belowright sb ' . s:buffer_map['breakpoints']
  exe 'belowright sb ' . s:buffer_map['locals']
  wincmd h
  exe 'belowright ' . winh2/2 . 'sp +b' . s:buffer_map['logs']
  set cole=2 cocu=nc
  exe bufwinnr(code_buf) . "wincmd w"
endfun

" tears down windows (and tabs) containing debug buffers
function! lldb#layout#teardown(...)
  if !exists('s:buffer_map') || empty(s:buffer_map)
    return
  endif
  let tabcount = tabpagenr('$')
  let bufnrs = values(s:buffer_map)
  for tabnr in range(tabcount, 1, -1)
    let blist = tabpagebuflist(tabnr)
    let bcount = len(blist)
    let bdcount = 0
    exe 'tabn ' . tabnr
    for bnr in blist
      if index(bufnrs, bnr) >= 0
        let bdcount += 1
        exe bufwinnr(bnr) . 'close'
      endif
    endfor
    if bcount < 2*bdcount && bcount > bdcount
      " close tab if majority of windows were lldb buffers
      tabc
    endif
  endfor
endfun

function! lldb#layout#signjump(bufnr, signid)
  if bufwinnr(a:bufnr) < 0
    let wnr = -1
    let ll_bufnrs = values(s:buffer_map)
    for i in range(winnr('$'))
      if index(ll_bufnrs, winbufnr(i+1)) < 0
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
