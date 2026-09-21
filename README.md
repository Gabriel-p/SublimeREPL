SublimeREPL for Sublime Text
===========================

SublimeREPL is a trimmed-down Sublime Text package that keeps only the
subprocess REPL support needed by `ProjectVenvReplCommand`.

Features
--------

* Launch an interactive Python REPL inside Sublime Text.
* Run the current Python file with the nearest `.venv/bin/python`, falling back
  to `/usr/bin/python3`.
* Keep the core `repl_open` and generic `subprocess` backend needed to host the
  REPL in a Sublime Text view.

Installation
============

1. Install Package Control.
2. Install `SublimeREPL`.
3. Restart Sublime Text.
4. Use it on Linux and configure `SublimeREPL` in `Preferences | Package Settings | SublimeREPL`.

Usage
=====

Use `Tools | SublimeREPL` or the command palette entries prefixed with
`SublimeREPL: Project Venv REPL` to launch one of the supported workflows:

* `Project Venv REPL - Run Current File`
* `Project Venv REPL - Interactive`

Keybindings
-----------

Inside an open REPL:

* <kbd>up</kbd>/<kbd>down</kbd> browse command history
* <kbd>enter</kbd> submits input
* <kbd>escape</kbd> clears current input
* <kbd>ctrl+l</kbd> clears the REPL view

Configuration
-------------

The default settings file documents the supported options, including:

* `default_extend_env`
* `open_repl_in_group`
* `view_auto_close`
* `history_arrows`

License
=======

Since version 1.2.0 SublimeREPL is licensed under GPL.
