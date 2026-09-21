from __future__ import absolute_import, unicode_literals, print_function, division
import sublime
import sublime_plugin

import os
import glob
import os.path
from functools import partial

SETTINGS_FILE = "SublimeREPL.sublime-settings"


def scan_for_virtualenvs(venv_paths):
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    found_dirs = set()
    for venv_path in venv_paths:
        p = os.path.expanduser(venv_path)
        pattern = os.path.join(p, "*", bin_dir, "activate_this.py")
        found_dirs.update(list(map(os.path.dirname, glob.glob(pattern))))
    return sorted(found_dirs)


class PythonVirtualenvRepl(sublime_plugin.WindowCommand):
    def _scan(self):
        venv_paths = sublime.load_settings(SETTINGS_FILE).get("python_virtualenv_paths", [])
        return scan_for_virtualenvs(venv_paths)

    def run_virtualenv(self, choices, index):
        if index == -1:
            return
        (name, directory) = choices[index]
        activate_file = os.path.join(directory, "activate_this.py")
        python_executable = os.path.join(directory, "python")
        path_separator = ":"
        if os.name == "nt":
            python_executable += ".exe"  # ;-)
            path_separator = ";"

        self.window.run_command("repl_open",
            {
                "encoding":"utf8",
                "type": "subprocess",
                "autocomplete_server": True,
                "extend_env": {
                    "PATH": directory + path_separator + "{PATH}",
                    "SUBLIMEREPL_ACTIVATE_THIS": activate_file,
                    "PYTHONIOENCODING": "utf-8"
                },
                "cmd": [python_executable, "-u", "${packages}/SublimeREPL/config/Python/ipy_repl.py"],
                "cwd": "$file_path",
                "encoding": "utf8",
                "syntax": "Packages/Python/Python.tmLanguage",
                "external_id": "python"
             })

    def run(self):
        choices = self._scan()
        nice_choices = [[path.split(os.path.sep)[-2], path] for path in choices]
        self.window.show_quick_panel(nice_choices, partial(self.run_virtualenv, nice_choices))




