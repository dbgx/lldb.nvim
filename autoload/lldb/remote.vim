function! s:llnotify(event, ...) abort
  if !exists('g:lldb#_channel_id')
    throw 'LLDB: channel id not defined!'
  endif
  let arg_list = extend([g:lldb#_channel_id, a:event], a:000)
  call call('rpcnotify', arg_list)
endfun

function! lldb#remote#init(chan_id)
  let g:lldb#_channel_id = a:chan_id
  au VimLeavePre * call <SID>llnotify('exit')
  call lldb#remote#define_commands()
endfun

function! s:llcomplete(arg, line, pos)
  let p = match(a:line, '^LL \+\zs')
  return rpcrequest(g:lldb#_channel_id, 'complete', a:arg, a:line[p : ], a:pos - p)
endfun

let s:ctrlchars = { 'BS': "\b",
                  \ 'CR': "\r",
                  \ 'EOT': "\x04",
                  \ 'LF': "\n",
                  \ 'NUL': "\0",
                  \ 'SPACE': " " }
function! s:stdinctrl(A, L, P)
  return keys(s:ctrlchars) + [ '--raw' ]
endfun

function! s:stdin(arg)
  if len(a:arg) > 0
    if has_key(s:ctrlchars, a:arg)
      return s:ctrlchars[a:arg]
    elseif a:arg == '--raw'
      return input('raw> ')
    else
      return input("Invalid input!\nraw> ")
    endif
  else
    return input('line> ') . "\n"
  endif
endfun

function! lldb#remote#get_modes()
  return rpcrequest(g:lldb#_channel_id, 'get_modes')
endfun

function! lldb#remote#define_commands()
  command!  LLrefresh   call <SID>llnotify("refresh")
  command!      -nargs=1    -complete=customlist,lldb#session#complete
          \ LLmode      call <SID>llnotify("mode", <f-args>)
  command!      -nargs=*    -complete=customlist,<SID>llcomplete
          \ LL          call <SID>llnotify("exec", <f-args>)
  command!      -nargs=?    -complete=customlist,<SID>stdinctrl
          \ LLstdin     call <SID>llnotify("stdin", <SID>stdin(<q-args>))

  nnoremap <silent> <Plug>LLBreakSwitch
          \ :call <SID>llnotify("breakswitch", bufnr("%"), getcurpos()[1])<CR>
  vnoremap <silent> <Plug>LLStdInSelected
          \ :<C-U>call <SID>llnotify("stdin", lldb#util#get_selection())<CR>
endfun
