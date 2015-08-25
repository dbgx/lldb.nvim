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

  " each key maps to [nargs, complete]; default: ['0', <s:llcomplete>]
  let s:cmd_map = { 'apropos':      ['1'],
                  \ 'breakpoint':   ['*'],
                  \ 'bt':           [],
                  \ 'command':      ['*'],
                  \ 'continue':     ['*'],
                  \ 'detach':       ['*'],
                  \ 'disassemble':  ['*'],
                  \ 'down':         ['?'],
                  \ 'expression':   ['*'],
                  \ 'finish':       ['*'],
                  \ 'frame':        ['*'],
                  \ 'help':         ['*'],
                  \ 'log':          ['*'],
                  \ 'next':         ['*'],
                  \ 'platform':     ['*'],
                  \ 'plugin':       ['*'],
                  \ 'po':           ['*'],
                  \ 'print':        ['*'],
                  \ 'process':      ['*'],
                  \ 'refresh':      [],
                  \ 'regexpbreak':  ['*'],
                  \ 'register':     ['*'],
                  \ 'settings':     ['*'],
                  \ 'source':       ['*'],
                  \ 'step':         ['*'],
                  \ 'target':       ['*'],
                  \ 'tbreak':       ['*'],
                  \ 'thread':       ['*'],
                  \ 'type':         ['*'],
                  \ 'up':           ['?'],
                  \ 'version':      [],
                  \ 'watchpoint':   ['*'],
                  \ 'mode':         ['1', 'customlist,lldb#session#complete']
                  \ }
  call lldb#remote#define_commands()
endfun

function! s:llcomplete(arg, line, pos)
  return rpcrequest(g:lldb#_channel_id, 'complete', a:arg, a:line, a:pos)
endfun

function! lldb#remote#define_commands()
  for [cmd, props] in items(s:cmd_map)
    let nargs = len(props) ? props[0] : '0'
    let copts = ''
    if nargs != '0'
      let copts = ' -nargs='.nargs
      let compl = len(props) == 1 ? 'customlist,<SID>llcomplete' : props[1]
      if len(compl)
        let compl = ' -complete=' . compl
      endif
      let copts .= compl
    endif
    exe 'command!' . copts . ' LL' . cmd . ' call <SID>llnotify("'. cmd . '", <f-args>)'
  endfor
  nnoremap <silent> <Plug>LLBreakSwitch
          \ :call <SID>llnotify("breakswitch", bufnr("%"), getcurpos()[1])<CR>
endfun

function! lldb#remote#undefine_commands()
  for cmd in keys(s:cmd_map)
    exe 'delcommand LL' . cmd
  endfor
  nunmap <Plug>LLBreakSwitch
endfun
