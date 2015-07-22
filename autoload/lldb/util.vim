function! lldb#util#signjump(bufnr, signid)
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

" stolen from http://stackoverflow.com/a/6271254/2849934
function! lldb#util#get_selection()
  let [lnum1, col1] = getpos("'<")[1:2]
  let [lnum2, col2] = getpos("'>")[1:2]
  let lines = getline(lnum1, lnum2)
  let lines[-1] = lines[-1][: col2 - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][col1 - 1:]
  return join(lines, "\n")
endfun
