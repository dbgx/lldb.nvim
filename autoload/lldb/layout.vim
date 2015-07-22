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
  let tabcount = 0
  for i in range(len(g:lldb#layout#cmds))
    if g:lldb#layout#cmds[i] == 'T'
      let tabcount += 1
    endif
  endfor
  if tabcount < tabpagenr('$')
    for i in range(tabcount)
      let tabnr = tabcount - i
      for bufnr in tabpagebuflist(tabnr)
        if index(g:lldb#layout#windows, bufname(bufnr)) >= 0
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
  for bname in g:lldb#_buffers
    let bnr = s:buffer_map[bname]
    exe 'silent bd ' . s:buffer_map[bname]
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
