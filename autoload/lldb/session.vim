function! s:complete_prefix(list, lead)
  if a:lead == ''
    return a:list
  endif
  let ret = []
  for c in a:list
    if c[:len(a:lead)-1] == a:lead
      call add(ret, c)
    endif
  endfor
  return ret
endfun

function! lldb#session#complete(ArgLead, CmdLine, CursorPos)
  let solid = substitute(a:CmdLine, '\\ ', '#', 'g')
  let tokens = split(solid, ' \+')
  let toknum = len(tokens)
  if solid[-1:] == ' '
    let toknum += 1
  endif
  if toknum == 2
    let subcmds = ['new', 'load', 'save', 'show']
    return s:complete_prefix(subcmds, a:ArgLead)
  endif
endfun
