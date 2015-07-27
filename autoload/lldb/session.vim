function! s:complete_file(path)
  let flist = glob(a:path, 0, 1)
  if len(flist) == 0
    let flist = glob(a:path . '*', 0, 1)
  elseif len(flist) == 1
    if flist[0] == a:path
      let flist = glob(a:path . '*', 0, 1)
      if len(flist) == 1
        let flist = glob(a:path . '/', 0, 1)
      endif
    endif
  endif
  let eflist = []
  for i in flist
    call add(eflist, escape(i, ' '))
  endfor
  return eflist
endfun

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
  let subcmd = tokens[1]
  if toknum == 3
    if subcmd == 'load' || subcmd == 'save'
      return s:complete_file(a:ArgLead)
    endif
  endif
endfun
