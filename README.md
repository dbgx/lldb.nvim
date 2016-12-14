# LLDB Neovim Frontend

This plugin provides LLDB debugger integration for Neovim ([demo gif][]) featuring:

* Elaborate view of debugger state
* Event-based, non-blocking UI
* Persistence of breakpoints and more across exits (session saving)
* Jump to code from Backtrace or Threads windows
* Modal approach: define modes and replay commands during mode-switches
* Tab-completion for LLDB commands

This plugin started out as a fork of https://github.com/gilligan/vim-lldb
which was forked from http://llvm.org/svn/llvm-project/lldb/trunk/utils/vim-lldb/

This plugin takes advantage of Neovim's job API to spawn a separate process
and communicates with the Neovim process using RPC calls.

[demo gif]: https://cloud.githubusercontent.com/assets/1436441/9903483/6ed0e9cc-5c94-11e5-8e4e-ce3b389df2d5.gif

## Prerequisites

* [Neovim](https://github.com/neovim/neovim)
* [Neovim python2-client](https://github.com/neovim/python-client) (release >= 0.1.6)
* [LLDB](http://lldb.llvm.org/)

## Installation

1. Using a plugin manager such as [vim-plug](https://github.com/junegunn/vim-plug):

   ```
       Plug 'critiqjo/lldb.nvim'
   ```

   Alternatively, clone this repo, and add the following line to your nvimrc:

   ```
       set rtp+=/path/to/lldb.nvim
   ```

2. Execute:

   ```
       :UpdateRemotePlugins
   ```

   and restart Neovim.

## Goals

The plugin is being developed keeping 3 broad goals in mind:

* **Ease of use**: Users with almost zero knowledge of command line debuggers should feel comfortable using this plugin.
* **Completeness**: Experienced users of LLDB should not feel restricted.
* **Customizability**: Users should be able to bend this plugin to their needs.

## Getting started

Here is a short screencast demonstrating the basics: [Youtube](https://youtu.be/rd654OxlmQs)

Also check out the getting started section from vim-docs (`:h lldb-start`).
For easy navigation of docs, I suggest using [viewdoc plugin](https://github.com/powerman/vim-plugin-viewdoc) by powerman.

## General Discussion

Please leave a feedback at the gitter page:
[![Join the chat at https://gitter.im/critiqjo/lldb.nvim](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/critiqjo/lldb.nvim?utm\_source=badge&utm\_medium=badge&utm\_campaign=pr-badge&utm\_content=badge)

## FAQ

#### I use Mac! \[...\]

You have 2 choices:

1. Use system python as the default python2 plugin provider of Neovim. Choosing this means you can use the LLDB that comes with XCode inside Neovim too.
   Read [this awesome blog post](http://blog.rplasil.name/2016/03/how-to-debug-neovim-python-remote-plugin.html) by [@Quiark](https://github.com/Quiark) for more details.
2. I don't like the system version of python -- it's 2.7.X, but I want 2.7.Y which has this feature Z.
   No worries (I hope), just install the brew version of LLVM with LLDB and python support. (Good luck! You will need it!)
   Also see [#15](https://github.com/critiqjo/lldb.nvim/issues/15) and [#18](https://github.com/critiqjo/lldb.nvim/issues/18) for all the gory details of troubleshooting.

#### This plugin does not work / stopped working!!

* Try `:UpdateRemotePlugins`, and restart Neovim.
* Try running the test script `test/run.sh`, and see how it goes.
  If you encounter an error during `import lldb`, see [#6 (comment)](https://github.com/critiqjo/lldb.nvim/issues/6#issuecomment-127192347).

Please file a bug report (also see `:help lldb-bugs`) if the problem persists.

#### Which all languages does LLDB support other than C/C++?

* Objective-C
* Swift (also see [swift-lldb](https://github.com/apple/swift-lldb))
* Rust (build: `rustc -g <file>`)
* Go (build: `go build -gcflag '-N -l' <file>`, see [this article's conclusion](http://blog.ralch.com/tutorial/golang-debug-with-lldb/#conclusion:1e1e92ac4b68191b3e5dc9a56a7ac9d2))
* and more?

#### The program counter is pointing to the wrong line in the source file at a breakpoint hit.

Try clang instead of gcc (fingers crossed). See [clang comparison](http://clang.llvm.org/comparison.html#gcc):

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
