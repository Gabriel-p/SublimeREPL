SublimeREPL for Sublime Text
===========================

SublimeREPL is a Linux-only, Python-only fork of the Sublime Text package for
working with a Python REPL inside an editor tab.

Features
--------

* Launch an interactive Python REPL inside Sublime Text.
* Run the current Python file.
* Launch the current Python file under PDB.
* Start IPython through the bundled `ipy_repl.py` helper.
* Discover local virtualenvs from `python_virtualenv_paths`.
* Send selections, lines, blocks, or entire files to the running Python REPL.
* Keep persistent history per Python REPL.

Installation
============

1. Install Package Control.
2. Install `SublimeREPL`.
3. Restart Sublime Text.
4. Use it on Linux and configure `SublimeREPL` in `Preferences | Package Settings | SublimeREPL`.

Usage
=====

Use `Tools | SublimeREPL | Python` or the command palette entries prefixed with
`SublimeREPL: Python` to launch one of the supported Python workflows:

* `Python`
* `Python - virtualenv`
* `Python - PDB current file`
* `Python - RUN current file`
* `Python - IPython`

Keybindings
-----------

Evaluate in REPL:

* <kbd>ctrl+,</kbd>, <kbd>s</kbd> Selection
* <kbd>ctrl+,</kbd>, <kbd>f</kbd> File
* <kbd>ctrl+,</kbd>, <kbd>l</kbd> Lines
* <kbd>ctrl+,</kbd>, <kbd>b</kbd> Block

Transfer to REPL without evaluating:

* <kbd>ctrl+shift+,</kbd>, <kbd>s</kbd> Selection
* <kbd>ctrl+shift+,</kbd>, <kbd>f</kbd> File
* <kbd>ctrl+shift+,</kbd>, <kbd>l</kbd> Lines
* <kbd>ctrl+shift+,</kbd>, <kbd>b</kbd> Block

Configuration
-------------

The default settings file documents the supported options, including:

* `default_extend_env`
* `python_virtualenv_paths`
* `open_repl_in_group`
* `show_transferred_text`
* `focus_view_on_transfer`

License
=======

Since version 1.2.0 SublimeREPL is licensed under GPL.
