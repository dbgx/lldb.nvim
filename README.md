# LLDB Neovim Frontend (under construction)

This plugin provides lldb debbuging integration including

    * breakpoints
    * watchpoints
    * threads view
    * locals view
    * and more ...

Arbitrary valid lldb commands can be invoked as well.

**NOTE** : This is a fork of https://github.com/gilligan/vim-lldb/, which is a fork of
the plugin that is part of the llvm distribution. The original can be found at
http://llvm.org/svn/llvm-project/lldb/trunk/utils/vim-lldb/

## Prerequisites

* [Neovim](https://github.com/neovim/neovim) with [python support](https://github.com/neovim/python-client).
* LLDB executable needs to be in the path

## Installation

Installation is easiest using a plugin manager such as vim-plug:

    Plug "critiqjo/lldb.nvim"

Of course you are free to manually copy the files to your vimrc folder if you prefer that for
whatever weird reason.


## Usage/Getting Help

Please refer to the vim help for a short 'getting started' section and
information on the available commands and configuration options. (:he lldb).
