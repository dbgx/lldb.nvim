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

"
" format of the command entries is as follows:
"   [ command name , completion function, nargs, python code, keymap]
"
let s:lldb_commands = [
\ ['Lhide',            's:CompleteWindow',  '1',   'ctrl.doHide("<args>")'],
\ ['Lshow',            's:CompleteWindow',  '1',   'ctrl.doShow("<args>")'],
\ ['Lstart',           '',                  '*',   'ctrl.doLaunch(True, "<args>")'],
\ ['Lrun',             '',                  '*',   'ctrl.doLaunch(False, "<args>")'],
\ ['Lattach',          '',                  '1',   'ctrl.doAttach("<args>")'],
\ ['Ldetach',          '',                  '0',   'ctrl.doDetach()'],
\ ['Lregexpattach',    's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-attach", "<args>")'],
\ ['Lregexpbreak',     's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-break", "<args>")'],
\ ['Lregexpbt',        's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-bt", "<args>")'],
\ ['Lregexpdown',      's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-down", "<args>")'],
\ ['Lregexptbreak',    's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-tbreak", "<args>")'],
\ ['Lregexpdisplay',   's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-display", "<args>")'],
\ ['Lregexpundisplay', 's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-undisplay", "<args>")'],
\ ['Lregexpup',        's:CompleteCommand', '*',   'ctrl.doCommand("_regexp-up", "<args>")'],
\ ['Lapropos',         's:CompleteCommand', '*',   'ctrl.doCommand("apropos", "<args>")'],
\ ['Lbacktrace',       's:CompleteCommand', '*',   'ctrl.doCommand("bt", "<args>")'],
\ ['Lbreakpoint',      's:CompleteCommand', '*',   'ctrl.doBreakpoint("<args>")', '<leader>lb'],
\ ["Lcommand",         "s:CompleteCommand", "*",   'ctrl.doCommand("command", "<args>")'],
\ ["Ldisassemble",     "s:CompleteCommand", "*",   'ctrl.doCommand("disassemble", "<args>")'],
\ ["Lexpression",      "s:CompleteCommand", "*",   'ctrl.doCommand("expression", "<args>")'],
\ ["Lhelp",            "s:CompleteCommand", "*",   'ctrl.doCommand("help", "<args>")'],
\ ["Llog",             "s:CompleteCommand", "*",   'ctrl.doCommand("log", "<args>")'],
\ ["Lplatform",        "s:CompleteCommand", "*",   'ctrl.doCommand("platform","<args>")'],
\ ["Lplugin",          "s:CompleteCommand", "*",   'ctrl.doCommand("plugin", "<args>")'],
\ ["Lprocess",         "s:CompleteCommand", "*",   'ctrl.doProcess("<args>")'],
\ ["Lregister",        "s:CompleteCommand", "*",   'ctrl.doCommand("register", "<args>")'],
\ ["Lscript",          "s:CompleteCommand", "*",   'ctrl.doCommand("script", "<args>")'],
\ ["Lsettings",        "s:CompleteCommand", "*",   'ctrl.doCommand("settings","<args>")'],
\ ["Lsource",          "s:CompleteCommand", "*",   'ctrl.doCommand("source", "<args>")'],
\ ["Ltype",            "s:CompleteCommand", "*",   'ctrl.doCommand("type", "<args>")'],
\ ["Lversion",         "s:CompleteCommand", "*",   'ctrl.doCommand("version", "<args>")'],
\ ["Lwatchpoint",      "s:CompleteCommand", "*",   'ctrl.doCommand("watchpoint", "<args>")'],
\ ["Lprint",           "s:CompleteCommand", "*",   'ctrl.doCommand("print", vim.eval("s:CursorWord("<args>")"))'],
\ ["Lpo",              "s:CompleteCommand", "*",   'ctrl.doCommand("po", vim.eval("s:CursorWord("<args>")"))'],
\ ["LpO",              "s:CompleteCommand", "*",   'ctrl.doCommand("po", vim.eval("s:CursorWORD("<args>")"))'],
\ ["Lbt",              "s:CompleteCommand", "*",   'ctrl.doCommand("bt", "<args>")'],
\ ["Lframe",           "s:CompleteCommand", "*",   'ctrl.doSelect("frame", "<args>")'],
\ ["Lup",              "s:CompleteCommand", "?",   'ctrl.doCommand("up", "<args>", print_on_success=False, goto_file=True)'],
\ ["Ldown",            "s:CompleteCommand", "?",   'ctrl.doCommand("down", "<args>", print_on_success=False, goto_file=True)'],
\ ["Lthread",          "s:CompleteCommand", "*",   'ctrl.doSelect("thread", "<args>")'],
\ ["Ltarget",          "s:CompleteCommand", "*",   'ctrl.doTarget("<args>")'],
\ ['Lcontinue',        "s:CompleteCommand", "*",   'ctrl.doContinue()', '<leader>lc'],
\ ['Lstepinst',        "",                  "0",   'ctrl.doStep(StepType.INSTRUCTION)'],
\ ['Lstepinstover',    "",                  "0",   'ctrl.doStep(StepType.INSTRUCTION_OVER)'],
\ ['Lstepin',          "",                  "0",   'ctrl.doStep(StepType.INTO)'],
\ ['Lstep',            "",                  "0",   'ctrl.doStep(StepType.INTO)', '<leader>li'],
\ ['Lnext',            "",                  "0",   'ctrl.doStep(StepType.OVER)', '<leader>ln'],
\ ['Lfinish',          "",                  "0",   'ctrl.doStep(StepType.OUT)'],
\ ['Lrefresh',         "",                  "0",   'ctrl.doRefresh()', '<leader>lr']
\]

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
    for cmd in s:lldb_commands
        let complFun = ''
        let nargs = ''
        if len(cmd[1]) > 0
            let complFun = '-complete=custom,' . cmd[1]
        endif
        if len(cmd[2]) > 0
            let nargs = '-nargs=' . cmd[2]
        endif
        execute 'command ' . complFun . ' ' . nargs . ' ' . cmd[0] . ' python ' . cmd[3]
    endfor
    " hack: service the LLDB event-queue when the cursor moves
    autocmd CursorMoved * :Lrefresh
    autocmd CursorHold  * :Lrefresh
    autocmd VimLeavePre * python ctrl.doExit()
endfunction
"

function lldb#createKeyMaps()
    for cmd in s:lldb_commands
        " only map what has been configured by the user
        if exists('g:lldb_map_' . cmd[0])
            execute 'nnoremap ' . eval('g:lldb_map_' . cmd[0]) . ' :' . cmd[0] . '<CR>'
        endif
    endfor
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

