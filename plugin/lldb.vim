" ---------------------------------------------------------------------
"  File:        lldb.vim
"  Description: LLDB Debugger Integration Plugin
"  Maintainer:  Tobias Pflug <tobias.pflug@gmail.com>
"  License:     Same License as Vim itself
"  --------------------------------------------------------------------

if (exists('g:loaded_lldb') && g:loaded_lldb) || v:version < 703 || &cp || !has('python')
    finish
endif
let g:loaded_lldb = 1

" Python module init {{{
function! lldb#pythonInit()
    execute 'python import sys'
    let python_module_dir = fnameescape(globpath(&runtimepath, 'python-vim-lldb'))
    execute 'python sys.path.append("' . python_module_dir . '")'
    execute 'pyfile ' . python_module_dir . '/plugin.py'
endfunction
" }}}


" Command registration {{{
function! lldb#createCommands()
    "
    " Register :L<Command>
    " The LLDB CommandInterpreter provides tab-completion in Vim's command mode.
    " FIXME: this list of commands, at least partially should be auto-generated
    "

    " Window show/hide commands
    command -complete=custom,s:CompleteWindow -nargs=1 Lhide               python ctrl.doHide('<args>')
    command -complete=custom,s:CompleteWindow -nargs=0 Lshow               python ctrl.doShow('<args>')

    " Launching convenience commands (no autocompletion)
    command -nargs=* Lstart                                                python ctrl.doLaunch(True,  '<args>')
    command -nargs=* Lrun                                                  python ctrl.doLaunch(False, '<args>')
    command -nargs=1 Lattach                                               python ctrl.doAttach('<args>')
    command -nargs=0 Ldetach                                               python ctrl.doDetach()

    " Regexp-commands: because vim's command mode does not support '_' or '-'
    " characters in command names, we omit them when creating the :L<cmd>
    " equivalents.
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpattach      python ctrl.doCommand('_regexp-attach', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpbreak       python ctrl.doCommand('_regexp-break', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpbt          python ctrl.doCommand('_regexp-bt', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpdown        python ctrl.doCommand('_regexp-down', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexptbreak      python ctrl.doCommand('_regexp-tbreak', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpdisplay     python ctrl.doCommand('_regexp-display', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpundisplay   python ctrl.doCommand('_regexp-undisplay', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregexpup          python ctrl.doCommand('_regexp-up', '<args>')

    command -complete=custom,s:CompleteCommand -nargs=* Lapropos           python ctrl.doCommand('apropos', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lbacktrace         python ctrl.doCommand('bt', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lbreakpoint        python ctrl.doBreakpoint('<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lcommand           python ctrl.doCommand('command', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Ldisassemble       python ctrl.doCommand('disassemble', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lexpression        python ctrl.doCommand('expression', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lhelp              python ctrl.doCommand('help', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Llog               python ctrl.doCommand('log', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lplatform          python ctrl.doCommand('platform','<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lplugin            python ctrl.doCommand('plugin', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lprocess           python ctrl.doProcess('<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lregister          python ctrl.doCommand('register', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lscript            python ctrl.doCommand('script', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lsettings          python ctrl.doCommand('settings','<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lsource            python ctrl.doCommand('source', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Ltype              python ctrl.doCommand('type', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lversion           python ctrl.doCommand('version', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=* Lwatchpoint        python ctrl.doCommand('watchpoint', '<args>')

    " Convenience (shortcut) LLDB commands
    command -complete=custom,s:CompleteCommand -nargs=* Lprint             python ctrl.doCommand('print', vim.eval("s:CursorWord('<args>')"))
    command -complete=custom,s:CompleteCommand -nargs=* Lpo                python ctrl.doCommand('po', vim.eval("s:CursorWord('<args>')"))
    command -complete=custom,s:CompleteCommand -nargs=* LpO                python ctrl.doCommand('po', vim.eval("s:CursorWORD('<args>')"))
    command -complete=custom,s:CompleteCommand -nargs=* Lbt                python ctrl.doCommand('bt', '<args>')

    " Frame/Thread-Selection (commands that also do an Uupdate but do not
    " generate events in LLDB)
    command -complete=custom,s:CompleteCommand -nargs=* Lframe             python ctrl.doSelect('frame', '<args>')
    command -complete=custom,s:CompleteCommand -nargs=? Lup                python ctrl.doCommand('up', '<args>',     print_on_success=False, goto_file=True)
    command -complete=custom,s:CompleteCommand -nargs=? Ldown              python ctrl.doCommand('down', '<args>', print_on_success=False, goto_file=True)
    command -complete=custom,s:CompleteCommand -nargs=* Lthread            python ctrl.doSelect('thread', '<args>')

    command -complete=custom,s:CompleteCommand -nargs=* Ltarget            python ctrl.doTarget('<args>')

    " Continue
    command -complete=custom,s:CompleteCommand -nargs=* Lcontinue          python ctrl.doContinue()

    " Thread-Stepping (no autocompletion)
    command -nargs=0 Lstepinst                                             python ctrl.doStep(StepType.INSTRUCTION)
    command -nargs=0 Lstepinstover                                         python ctrl.doStep(StepType.INSTRUCTION_OVER)
    command -nargs=0 Lstepin                                               python ctrl.doStep(StepType.INTO)
    command -nargs=0 Lstep                                                 python ctrl.doStep(StepType.INTO)
    command -nargs=0 Lnext                                                 python ctrl.doStep(StepType.OVER)
    command -nargs=0 Lfinish                                               python ctrl.doStep(StepType.OUT)

    " hack: service the LLDB event-queue when the cursor moves
    " FIXME: some threaded solution would be better...but it
    "        would have to be designed carefully because Vim's APIs are non threadsafe;
    "        use of the vim module **MUST** be restricted to the main thread.
    command -nargs=0 Lrefresh python ctrl.doRefresh()
    autocmd CursorMoved * :Lrefresh
    autocmd CursorHold  * :Lrefresh
    autocmd VimLeavePre * python ctrl.doExit()
endfunction
"

function lldb#createKeyMaps()
    if !(exists('g:lldb_vim_map_keys'))
        let g:lldb_vim_map_keys = 1
    endif
    if g:lldb_vim_map_keys
        autocmd FileType c,cpp nnoremap <leader>lb :Lbreakpoint<CR>
        autocmd FileType c,cpp nnoremap <leader>ls :Lstep<CR>
        autocmd FileType c,cpp nnoremap <leader>ln :Lnext<CR>
        autocmd FileType c,cpp nnoremap <leader>lc :Lcontinue<CR>
        autocmd FileType c,cpp nnoremap <leader>lp :Lprint<CR>
    endif
endfunction

function! s:InitLldbPlugin()
    call lldb#pythonInit()
    call lldb#createCommands()
    call lldb#createKeyMaps()
endfunction()
" }}}


" Command Completion Functions {{{
function! s:CompleteCommand(A, L, P)
    python << EOF
    a = vim.eval("a:A")
    l = vim.eval("a:L")
    p = vim.eval("a:P")
    returnCompleteCommand(a, l, p)
EOF
endfunction()

function! s:CompleteWindow(A, L, P)
    python << EOF
    a = vim.eval("a:A")
    l = vim.eval("a:L")
    p = vim.eval("a:P")
    returnCompleteWindow(a, l, p)
EOF
endfunction()

" Returns cword if search term is empty
function! s:CursorWord(term)
    return empty(a:term) ? expand('<cword>') : a:term
endfunction()

" Returns cleaned cWORD if search term is empty
function! s:CursorWORD(term)
    " Will strip all non-alphabetic characters from both sides
    return empty(a:term) ?  substitute(expand('<cWORD>'), '^\A*\(.\{-}\)\A*$', '\1', '') : a:term
endfunction()
" }}}


call s:InitLldbPlugin()

