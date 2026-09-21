.. toctree::
   :maxdepth: 2

SublimeREPL
===========

SublimeREPL is a trimmed Sublime Text plugin focused on the
``ProjectVenvReplCommand`` workflow: opening a subprocess-backed Python REPL in
an editor tab by locating ``.venv/bin/python`` from the current file and
falling back to ``/usr/bin/python3``.

Quick Start
-----------

Launch the remaining workflow from either:

* ``Tools > SublimeREPL > Project Venv REPL - Run Current File``
* ``Tools > SublimeREPL > Project Venv REPL - Interactive``
* the command palette entries prefixed with ``SublimeREPL: Project Venv REPL``

Once a REPL is open, the remaining package functionality is the generic REPL
view and subprocess backend required to host that session.

Keyboard shortcuts
------------------

REPL keys
^^^^^^^^^

+---------------+----------------------------------+-------------------------------------------------+
| Key           | Command used                     | Meaning                                         |
+===============+==================================+=================================================+
| Up            | repl_view_previous               | Walk back to previous input, with autocomplete  |
+---------------+----------------------------------+-------------------------------------------------+
| Alt+p         | repl_view_previous               | Walk back to previous input, no autocomplete    |
+---------------+----------------------------------+-------------------------------------------------+
| Down          | repl_view_next                   | Walk back to next input, with autocomplete      |
+---------------+----------------------------------+-------------------------------------------------+
| Alt+n         | repl_view_next                   | Walk back to next input, no autocomplete        |
+---------------+----------------------------------+-------------------------------------------------+
| Enter         | repl_enter                       | Send current line to REPL                       |
+---------------+----------------------------------+-------------------------------------------------+
| Esc           | repl_escape                      | Clear REPL input                                |
+---------------+----------------------------------+-------------------------------------------------+
| Ctrl+l        | repl_clear                       | Clear REPL screen                               |
+---------------+----------------------------------+-------------------------------------------------+

ProjectVenvReplCommand
----------------------

``project_venv_repl.py`` provides a single ``TextCommand`` that:

* saves the current file before the non-interactive run-current-file workflow
* walks upward from the current file looking for ``.venv/bin/python``
* falls back to ``/usr/bin/python3``
* opens the REPL through ``window.run_command("repl_open", ...)``
* runs either the current file or an interactive ``python -u -i`` session

Configuration
-------------

The default ``SublimeREPL.sublime-settings`` file documents the remaining
subprocess REPL options, including environment extension, REPL view behavior,
and history navigation keys.
