.. toctree::
   :maxdepth: 2

SublimeREPL
===========

SublimeREPL is a Linux-only Sublime Text plugin focused on running Python inside
a normal editor tab. It supports launching an interactive Python REPL, IPython,
virtualenv-backed Python sessions, running the current file, and debugging the
current file with PDB.

Quick Start
-----------

Launch Python from either:

* ``Tools > SublimeREPL > Python``
* the command palette entries prefixed with ``SublimeREPL: Python``

The bundled Python integration provides these entry points:

* Python
* Python - virtualenv
* Python - PDB current file
* Python - RUN current file
* Python - IPython

Once a Python REPL is open, you can send source text from a Python buffer to
that REPL for execution or transfer.

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
| Shift+Ctrl+c  | subprocess_repl_send_signal      | Send SIGINT to REPL                             |
+---------------+----------------------------------+-------------------------------------------------+

Source buffer keys
^^^^^^^^^^^^^^^^^^

+---------------+----------------------------------------------------+
| Key           | Meaning                                            |
+===============+====================================================+
| Ctrl+, b      | Send the current bracket-selected block to REPL    |
+---------------+----------------------------------------------------+
| Ctrl+, s      | Send the selection to REPL                         |
+---------------+----------------------------------------------------+
| Ctrl+, f      | Send the current file to REPL                      |
+---------------+----------------------------------------------------+
| Ctrl+, l      | Send the current line to REPL                      |
+---------------+----------------------------------------------------+

Python features
---------------

The Python integration keeps support for:

* standard interactive Python subprocesses
* local virtualenv discovery via ``python_virtualenv_paths``
* IPython via ``config/Python/ipy_repl.py``
* launching the current file with ``python -u``
* launching the current file under ``python -m pdb``
* persistent command history and text transfer

Configuration
-------------

The default ``SublimeREPL.sublime-settings`` file documents the supported
options for Python workflows, including environment extension, virtualenv
search paths, history handling, and REPL view behavior.
