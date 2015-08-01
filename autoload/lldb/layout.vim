function! lldb#layout#init_buffers()
  let s:buffers = [ 'backtrace', 'breakpoints', 'disassembly', 'locals', 'registers', 'threads' ]
  let s:buffer_map = {}
  let u_bnr = bufnr('%')
  for bname in s:buffers
    let bnr = bufnr('lldb_' . bname, 1)
    call setbufvar(bnr, '&bt', 'nofile')
    call setbufvar(bnr, '&swf', 0)
    call setbufvar(bnr, '&ma', 0)
    exe 'silent b ' . bnr
    call setbufvar(bnr, '&nu', 0)
    call setbufvar(bnr, '&rnu', 0)
    call setbufvar(bnr, '&bl', 0)
    let s:buffer_map[bname] = bnr
  endfor
  exe 'b ' . u_bnr
  return s:buffer_map
endfun

function! lldb#layout#setup()
  if !exists('s:buffer_map') || empty(s:buffer_map)
    call lldb#layout#init_buffers()
  endif
  let code_buf = bufnr('%')
  if index(s:buffers, code_buf) >= 0
    let code_buf = '[No Name]'
  endif
  exe '0tab sb ' . code_buf
  exe 'belowright vertical sb ' . s:buffer_map['backtrace']
  exe 'belowright sb ' . s:buffer_map['breakpoints']
  exe 'belowright sb ' . s:buffer_map['disassembly']
  exe 'belowright vertical sb ' . s:buffer_map['locals']
  wincmd k
  exe 'belowright vertical sb ' . s:buffer_map['registers']
  wincmd k
  exe 'belowright vertical sb ' . s:buffer_map['threads']
  exe bufwinnr(code_buf) . "wincmd w"
endfun

" ignores all arguments
function! lldb#layout#teardown(...)
  if !exists('s:buffer_map') || empty(s:buffer_map)
    return
  endif
  let tabcount = tabpagenr('$')
  let bufnrs = values(s:buffer_map)
  for i in range(tabcount)
    let tabnr = tabcount - i
    let blist = tabpagebuflist(tabnr)
    let bcount = 0
    exe 'tabn ' . tabnr
    for bnr in blist
      if index(bufnrs, bnr) >= 0
        let bcount += 1
        exe bufwinnr(bnr) . 'close'
      endif
    endfor
    if len(tabpagebuflist(tabnr)) < bcount
      " close tab if majority of windows were lldb buffers
      tabc
    endif
  endfor
endfun
