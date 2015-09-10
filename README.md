# LLDB Neovim Frontend

This plugin provides LLDB debugger integration for Neovim, featuring:

* Breakpoints and program counter displayed as signs
* Buffers showing backtrace, breakpoints, threads, local variables, registers and disassembly
* Supports almost all LLDB commands from vim-command line (with tab-completion)
* Event-based UI updates
* Non-blocking UI
* Customizable Layout

**NOTE** : This is a fork of https://github.com/gilligan/vim-lldb/, which is a fork of
the plugin that is part of the llvm distribution. The original can be found at
http://llvm.org/svn/llvm-project/lldb/trunk/utils/vim-lldb/

## Prerequisites

* [Neovim](https://github.com/neovim/neovim)
* [Neovim python2-client](https://github.com/neovim/python-client) (release >= 0.0.38)
* [LLDB](http://lldb.llvm.org/)

## Installation

Installation is easiest using a plugin manager such as [vim-plug](https://github.com/junegunn/vim-plug):
```
    Plug "critiqjo/lldb.nvim"
```
Or manually copy the files to your `~/.nvimrc` folder.

Note: After installing (or updating) a plugin that uses Neovim's remote plugin API,
you (might) have to execute:
```
    :UpdateRemotePlugins
```
and restart Neovim.

## Goals

The plugin is being developed keeping 3 broad goals in mind:

* **Ease of use**: Users with almost zero knowledge of command line debuggers should feel comfortable using this plugin.
* **Completeness**: Experienced users of LLDB should not feel restricted.
* **Customizability**: Users should be able to bend this plugin easily in the following aspects:
    * Display of debugger status (eg. customisable disassembly view)
    * Visual layout or window management
    * Key-bindings

As of 0.3 release, none of these goals are met.

## Getting started

Watch a [demo video](https://youtu.be/aXSNhTH1Co4), or refer to the getting
started section in the vim-docs (`:h lldb-start`).

## General Discussion

[![Join the chat at https://gitter.im/critiqjo/lldb.nvim](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/critiqjo/lldb.nvim?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## FAQ

#### After the recent update, [command] stopped working!

Have you tried `:UpdateRemotePlugins` and restarting Neovim? If you did, and
the problem persists, please file a bug report (also see `:help lldb-bugs`).
(I forget this all the time!)

#### How do I attach to a running process?

To be able to attach, the "attacher" needs to have special permissions. The
easiest method is to run a debug server as 'sudo' and connect to it.
See the question below.

#### Remote debugging does not work!!

I haven't been able to get `gdbserver`, `lldb-gdbserver` or `lldb-server gdbserver`
to work properly with the python API. But the following works; run:

```
# use sudo if you want to attach to a running process
$ lldb-server platform --listen localhost:2345
```

The above command will start the server in platform mode and listen for connections
on port 2345. Now, from the client (the plugin), run:

```
(lldb) platform select remote-linux
(lldb) platform connect connect://localhost:2345
(lldb) process attach --name cat
```

For more info on this, see [Remote Debugging](http://lldb.llvm.org/remote.html).
