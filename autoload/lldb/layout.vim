function! lldb#layout#init_buffers()
  let s:buffer_map = {}
  let u_bnr = bufnr('%')
  for bname in g:lldb#_buffers
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
  if a:0 == 0 || (a:0 > 0 && !a:1)
    return
  endif
  for bnr in bufnrs
    exe 'silent bd ' . bnr
    call setbufvar(bnr, '&bt', 'nofile')
  endfor
  let s:buffer_map = {}
endfun

function! lldb#layout#update()
  if !exists('s:buffer_map') || empty(s:buffer_map)
    call lldb#layout#init_buffers()
  endif
  let code_buf = bufname('%')
  if index(g:lldb#_buffers, code_buf) >= 0
    let code_buf = '[No Name]'
  endif
  let c = g:lldb#layout#cmds
  let w = g:lldb#layout#windows
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
