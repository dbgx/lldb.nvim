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
    let subcmds = ['new', 'load']
    call extend(subcmds, ['mode', 'save', 'show']) "if session active
    return s:complete_prefix(subcmds, a:ArgLead)
  endif
  let subcmd = tokens[1]
  if toknum == 3
    if subcmd == 'load' || subcmd == 'save'
      return s:complete_file(a:ArgLead)
    elseif subcmd == 'mode'
      let modcmds = ['code', 'debug']
      return s:complete_prefix(modcmds, a:ArgLead)
    endif
  endif
endfun

function! s:find_xfiles()
  let files = split(system('find bin build/bin target/debug . -not -name "*.sh"'.
        \ ' -maxdepth 1 -perm -111 -type f -print 2>/dev/null'))
  if len(files) > 0
    return files[0]
  else
    return ''
  endif
endfun

function! lldb#session#new(has_state)
  if a:has_state && input('Throw away the current session? (y/n) ', 'n') != 'y'
    return
  endif
  let session_file = input('Write session file to: ', g:lldb#session#file, 'file')
  let target = input('Path to target executable: ', s:find_xfiles(), 'file')
  return { "_file": session_file,
         \ "_file_bak": g:lldb#session#file_bak,
         \ "target": target
         \ }
endfun
