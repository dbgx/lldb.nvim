" stolen from http://stackoverflow.com/a/6271254/2849934
function! lldb#util#get_selection()
  let [lnum1, col1] = getpos("'<")[1:2]
  let [lnum2, col2] = getpos("'>")[1:2]
  let lines = getline(lnum1, lnum2)
  let lines[-1] = lines[-1][: col2 - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][col1 - 1:]
  return join(lines, "\n")
endfun

function! lldb#util#buffer_do(bufnr, cmd)
  let old_wnr = winnr()
  for wnr in range(winnr('$'))
    if winbufnr(wnr) == a:bufnr
      exe wnr . "windo " . a:cmd
    endif
  endfor
  exe old_wnr . "wincmd w"
endfun
