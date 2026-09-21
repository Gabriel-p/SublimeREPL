import os

import sublime_plugin


class ProjectVenvReplCommand(sublime_plugin.TextCommand):
    """
    Starts a SublimeREPL, searching upward for a .venv/bin/python interpreter
    from the current file's location.
    """

    def run(self, edit, interactive=False, name="python"):
        window = self.view.window()
        for view in window.views():
            if view.is_dirty() and view.file_name():
                view.run_command("save")

        file_name = self.view.file_name()
        python_path = self.get_venv_python(file_name)

        if interactive is False and file_name:
            cmd_list = [python_path, "-u", file_name]
        else:
            cmd_list = [python_path, "-u", "-i"]

        self.repl_open(cmd_list=cmd_list, name=name, file_name=file_name)

    def get_venv_python(self, start_path):
        if not start_path:
            return "/usr/bin/python3"

        dir_path = os.path.dirname(start_path)

        while True:
            candidate = os.path.join(dir_path, ".venv", "bin", "python")
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
            parent = os.path.dirname(dir_path)
            if parent == dir_path:
                break
            dir_path = parent

        return "/usr/bin/python3"

    def repl_open(self, cmd_list, name, file_name):
        self.view.window().run_command(
            "repl_open",
            {
                "encoding": "utf8",
                "type": "subprocess",
                "cmd": cmd_list,
                "cwd": os.path.dirname(file_name) if file_name else os.path.expanduser("~"),
                "syntax": "Packages/Python/Python.sublime-syntax",
                "external_id": name,
            },
        )
