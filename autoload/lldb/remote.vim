function! lldb#remote#init(chan_id)
  let g:lldb#_channel_id = a:chan_id
  au VimLeavePre * call rpcnotify(g:lldb#_channel_id, 'exit')
endfun
