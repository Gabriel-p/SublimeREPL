SublimeREPL-py
==============

This is a heavily stripped down version of the [SublimeREPL](https://github.com/wuub/SublimeREPL) package.
It is intended to be used to run Python in a Linux system.

Set key bindings to run either a Python REPL with the currently open file or an
interactive REPL without any file. E.g.:

```
// Runs currently open file in REPL
{
    "keys": [
        "f5"
    ],
    "command": "run_python_repl"
},
// Runs interactive REPL without any file
{
    "keys": [
        "f4"
    ],
    "command": "run_python_repl",
    "args": {
        "interactive": true
    }
}
```