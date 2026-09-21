import os

import sublime_plugin


class ProjectVenvReplCommand(sublime_plugin.TextCommand):
    """
    Starts a SublimeREPL, searching upward for a .venv/bin/python interpreter
    from the current file's location.
    """

    def run(self, edit, interactive=False, name=" "):
        window = self.view.window()
        for view in window.views():
            if view.is_dirty() and view.file_name():
                view.run_command("save")

        python_path = self.get_venv_python(self.view.file_name())
        print(f"Using Python interpreter: {python_path}")

        if interactive is False:
            path, filename = os.path.split(self.view.file_name())
            open_file = path + "/" + filename
            cmd_list = [python_path, "-u", open_file]
        else:
            cmd_list = [python_path, "-u", "-i"]

        self.repl_open(cmd_list=cmd_list, name=name)

    def get_venv_python(self, start_path):
        if not start_path:
            return "/usr/bin/python3"

        dir_path = os.path.dirname(start_path)

        while dir_path != os.path.dirname(dir_path):
            candidate = os.path.join(dir_path, ".venv", "bin", "python")
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
            dir_path = os.path.dirname(dir_path)

        return "/usr/bin/python3"

    def repl_open(self, cmd_list, name):
        self.view.window().run_command(
            "repl_open",
            {
                "encoding": "utf8",
                "type": "subprocess",
                "cmd": cmd_list,
                "cwd": "$file_path",
                "syntax": "Packages/Python/Python.sublime-syntax",
                "external_id": name,
            },
        )
