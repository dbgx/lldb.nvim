function! lldb#remote#__notify(event, ...) abort
  if !exists('g:lldb#_channel_id')
    throw 'LLDB: channel id not defined!'
  endif
  let arg_list = extend([g:lldb#_channel_id, a:event], a:000)
  call call('rpcnotify', arg_list)
endfun

function! lldb#remote#init(chan_id)
  let g:lldb#_channel_id = a:chan_id
  au VimLeavePre * call lldb#remote#__notify('exit')
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
function! s:stdincompl(A, L, P)
  return keys(s:ctrlchars) + [ '--raw' ]
endfun

function! lldb#remote#stdin_prompt(...)
  let strin = ''
  if a:0 == 1 && len(a:1) > 0
    if has_key(s:ctrlchars, a:1)
      let strin = s:ctrlchars[a:1]
    elseif a:1 == '--raw'
      let strin = input('raw> ')
    else
      let strin = input("Invalid argument!\nline> ", a:1) . "\n"
    endif
  elseif a:0 > 1
    let strin = input("Too many arguments!\nline> ", join(a:000, ' ')) . "\n"
  else
    let strin = input('line> ') . "\n"
  endif
  call lldb#remote#__notify("stdin", strin)
endfun

function! lldb#remote#get_modes()
  if exists('g:lldb#_channel_id')
    return rpcrequest(g:lldb#_channel_id, 'get_modes')
  else
    return []
  endif
endfun

function! lldb#remote#define_commands()
  command!  LLrefresh   call lldb#remote#__notify("refresh")
  command!      -nargs=1    -complete=customlist,lldb#session#complete
          \ LLmode      call lldb#remote#__notify("mode", <f-args>)
  command!      -nargs=*    -complete=customlist,<SID>llcomplete
          \ LL          call lldb#remote#__notify("exec", <f-args>)
  command!      -nargs=?    -complete=customlist,<SID>stdincompl
          \ LLstdin     call lldb#remote#stdin_prompt(<f-args>)

  nnoremap <silent> <Plug>LLBreakSwitch
          \ :call lldb#remote#__notify("breakswitch", bufnr("%"), getcurpos()[1])<CR>
  vnoremap <silent> <Plug>LLStdInSelected
          \ :<C-U>call lldb#remote#__notify("stdin", lldb#util#get_selection())<CR>
endfun
