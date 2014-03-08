LLDB Vim Frontend
=================

This plugin provides lldb debbuging integration including

    * breakpoints
    * watchpoints
    * threads view
    * locals view
    * and more ...

Arbitrary valid lldb commands can be invoked as well.

**NOTE** : This is a fork of the plugin which is part of the llvm distribution. The original
can be found at http://llvm.org/svn/llvm-project/lldb/trunk/utils/vim-lldb/.

![](https://raw.github.com/gilligan/vim-lldb/master/vim-lldb.png)

Prerequisites
-------------

* vim >= 7.3 on Linux or OSX with python support built in
* lldb executable needs to be in the path

Installation
------------

Installation is easiest using a package manager such as vundle:

    Bundle "gilligan/vim-lldb"

Of course you are free to manually copy the files to your vimrc folder if you prefer that for
whatever weird reason.


Usage/Getting Help
------------------

Please refer to the vim help for a short 'getting started' section and
information on the available commands and configuration options. (:he lldb).
