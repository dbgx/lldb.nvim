

## Is upstream-bug?

When filing a bug-report, make sure it is indeed a bug in this plugin, and not
an upstream (lldb) bug. To that end, please execute the following script in
your Python2 REPL, and provide its output:

```py
import lldb

dbg = lldb.SBDebugger.Create()
ci = dbg.GetCommandInterpreter()

def execute(command):
    res = lldb.SBCommandReturnObject()
    ci.HandleCommand(command, res)
    print(res.Succeeded(), res.GetOutput(), res.GetError())

# now execute each command as follows:
execute("target create ...")
execute("your command here")
```

```
...output here...
```

<!--
  If the error was reproduced in REPL, you can be sure that this is an upstream
  bug, and you are welcome to add a comment about it at
  https://github.com/dbgx/lldb.nvim/issues/59

  If you find it hard to mimic the steps using REPL, then file an issue anyway
  and we'll see.
-->
