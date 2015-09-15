# LLDB Neovim Frontend

This plugin provides LLDB debugger integration for Neovim, featuring:

* Buffers showing debugger state: backtrace, breakpoints etc.
* Event-based, non-blocking UI
* Breakpoints persistence across exits
* Modal approach: define modes and replay commands during mode-switches
* Tab-completion for LLDB commands

This plugin started out as a fork of https://github.com/gilligan/vim-lldb
which was forked from http://llvm.org/svn/llvm-project/lldb/trunk/utils/vim-lldb/

A lot of refactoring, performance improvements, and many new features were
added which would have been very hard (if not impossible) to implement as a
standard Vim plugin.

This plugin takes advantage of Neovim's job API to spawn a separate process
and communicates with the Neovim process using RPC calls.

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

As of 0.7 release, I believe **Completeness** is within reach, and a glimpse of the rest is in view.

## Getting started

A demo screencast will be posted soon, until then please refer to the getting started section in the vim-docs (`:h lldb-start`).
For easy navigation of vim documentaion, I suggest using [viewdoc plugin](https://github.com/powerman/vim-plugin-viewdoc) by powerman.

## General Discussion

[![Join the chat at https://gitter.im/critiqjo/lldb.nvim](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/critiqjo/lldb.nvim?utm\_source=badge&utm\_medium=badge&utm\_campaign=pr-badge&utm\_content=badge)

## FAQ

#### After the recent update, [command] stopped working!

Have you tried `:UpdateRemotePlugins` and restarting Neovim? If you did, and
the problem persists, please file a bug report (also see `:help lldb-bugs`).

#### The program counter is pointing to the wrong line in the source file at a breakpoint hit.

Use clang compiler instead of gcc. Quote from [clang comparison](http://clang.llvm.org/comparison.html#gcc):

>Clang does not implicitly simplify code as it parses it like GCC does. Doing so causes many problems for source analysis tools.

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

# in older versions of lldb, use this instead
$ lldb-platform --listen localhost:2345
```

The above command will start the server in platform mode and listen for connections
on port 2345. Now, from the client (the plugin), run:

```
(lldb) platform select remote-linux
(lldb) platform connect connect://localhost:2345
(lldb) process attach --name cat
```

For more info on this, see [Remote Debugging](http://lldb.llvm.org/remote.html).
