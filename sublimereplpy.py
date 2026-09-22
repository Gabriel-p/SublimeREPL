# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.

import os
import os.path

# try:
import queue
import re
import threading
import traceback

import sublime
import sublime_plugin

from . import repls

unicode_type = str

SETTINGS_FILE = "SublimeREPL-py.sublime-settings"
# SUBLIME2 = sublime.version() < "3000"

RESTART_MSG = """
#############
## RESTART ##
#############
"""


class ReplInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, pos, text):
        self.view.set_read_only(False)  # make sure view is writable
        self.view.insert(edit, int(pos), text)


class ReplEraseTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, start, end):
        self.view.set_read_only(False)  # make sure view is writable
        self.view.erase(edit, sublime.Region(int(start), int(end)))


class ReplPass(sublime_plugin.TextCommand):
    def run(self, edit):
        pass


class ReplReader(threading.Thread):
    def __init__(self, repl):
        super().__init__()
        self.repl = repl
        self.daemon = True
        self.queue = queue.Queue()

    def run(self):
        r = self.repl
        q = self.queue
        while True:
            result = r.read()
            q.put(result)
            if result is None:
                break


class HistoryMatchList:
    def __init__(self, command_prefix, commands):
        self._command_prefix = command_prefix
        self._commands = commands
        self._cur = len(commands)  # no '-1' on purpose

    def current_command(self):
        if not self._commands:
            return ""
        return self._commands[self._cur]

    def prev_command(self):
        self._cur = max(0, self._cur - 1)
        return self.current_command()

    def next_command(self):
        self._cur = min(len(self._commands) - 1, self._cur + 1)
        return self.current_command()


class History:
    def __init__(self):
        self._last = None

    def push(self, command):
        cmd = command.rstrip()
        if not cmd or cmd == self._last:
            return
        self.append(cmd)
        self._last = cmd

    def append(self, cmd):
        raise NotImplementedError()

    def match(self, command_prefix):
        raise NotImplementedError()


class MemHistory(History):
    def __init__(self):
        super().__init__()
        self._stack = []

    def append(self, cmd):
        self._stack.append(cmd)

    def match(self, command_prefix):
        matching_commands = []
        for cmd in self._stack:
            if cmd.startswith(command_prefix):
                matching_commands.append(cmd)
        return HistoryMatchList(command_prefix, matching_commands)


class ReplView:
    def __init__(self, view, repl, syntax, repl_restart_args):
        self.repl = repl
        self._view = view
        self._window = view.window()
        self._repl_launch_args = repl_restart_args
        # list of callable(repl) to handle view close events
        self.call_on_close = []

        if syntax:
            view.set_syntax_file(syntax)
        self._output_end = view.size()
        self._prompt_size = 0

        self._repl_reader = ReplReader(repl)
        self._repl_reader.start()

        settings = sublime.load_settings(SETTINGS_FILE)

        view.settings().set("repl_external_id", repl.external_id)
        view.settings().set("repl_id", repl.id)
        view.settings().set("repl", True)
        # view.settings().set("repl_sublime2", SUBLIME2)
        if repl.allow_restarts():
            view.settings().set("repl_restart_args", repl_restart_args)

        rv_settings = settings.get("repl_view_settings", {})
        for setting, value in list(rv_settings.items()):
            view.settings().set(setting, value)

        view.settings().set("history_arrows", settings.get("history_arrows", True))

        self._history = MemHistory()
        self._history_match = None

        self._filter_color_codes = settings.get("filter_ascii_color_codes")

        # optionally move view to a different group
        # find current position of this replview
        (group, index) = self._window.get_view_index(view)

        # get the view that was focussed before the repl was opened.
        # we'll have to focus this one briefly to make sure it's in the
        # foreground again after moving the replview away
        oldview = self._window.views_in_group(group)[max(0, index - 1)]

        target = settings.get("open_repl_in_group")

        # either the target group is specified by index
        if isinstance(target, int):
            if 0 <= target < self._window.num_groups() and target != group:
                self._window.set_view_index(
                    view, target, len(self._window.views_in_group(target))
                )
                self._window.focus_view(oldview)
                self._window.focus_view(view)
        ## or, if simply set to true, move it to the next group from the currently active one
        elif target and group + 1 < self._window.num_groups():
            self._window.set_view_index(
                view, group + 1, len(self._window.views_in_group(group + 1))
            )
            self._window.focus_view(oldview)
            self._window.focus_view(view)

        # begin refreshing attached view
        self.update_view_loop()

    def on_backspace(self):
        if self.delta < 0:
            self._view.run_command("left_delete")

    def on_ctrl_backspace(self):
        if self.delta < 0:
            self._view.run_command("delete_word", {"forward": False, "sub_words": True})

    def on_left(self):
        if self.delta != 0:
            self._window.run_command(
                "move", {"by": "characters", "forward": False, "extend": False}
            )

    def on_shift_left(self):
        if self.delta != 0:
            self._window.run_command(
                "move", {"by": "characters", "forward": False, "extend": True}
            )

    def on_home(self):
        if self.delta > 0:
            self._window.run_command("move_to", {"to": "bol", "extend": False})
        else:
            for i in range(abs(self.delta)):
                self._window.run_command(
                    "move", {"by": "characters", "forward": False, "extend": False}
                )

    def on_shift_home(self):
        if self.delta > 0:
            self._window.run_command("move_to", {"to": "bol", "extend": True})
        else:
            for i in range(abs(self.delta)):
                self._window.run_command(
                    "move", {"by": "characters", "forward": False, "extend": True}
                )

    def on_selection_modified(self):
        self._view.set_read_only(self.delta > 0)

    def on_close(self):
        self.repl.close()
        for fun in self.call_on_close:
            fun(self)

    def clear(self, edit):
        self.escape(edit)
        self._view.erase(edit, self.output_region)
        self._output_end = self._view.sel()[0].begin()

    def escape(self, edit):
        self._view.set_read_only(False)
        self._view.erase(edit, self.input_region)
        self._view.show(self.input_region)

    def enter(self):
        v = self._view
        if v.sel()[0].begin() != v.size():
            v.sel().clear()
            v.sel().add(sublime.Region(v.size()))

        l = self._output_end

        self.push_history(self.user_input)  # don't include cmd_postfix in history
        v.run_command("insert", {"characters": self.repl.cmd_postfix})
        command = self.user_input
        self.adjust_end()

        if self.repl.apiv2:
            self.repl.write(command, location=l)
        else:
            self.repl.write(command)

    def previous_command(self, edit):
        self._view.set_read_only(False)
        self.ensure_history_match()
        self.replace_current_input(edit, self._history_match.prev_command())
        self._view.show(self.input_region)

    def next_command(self, edit):
        self._view.set_read_only(False)
        self.ensure_history_match()
        self.replace_current_input(edit, self._history_match.next_command())
        self._view.show(self.input_region)

    def update_view(self, view):
        """If projects were switched, a view could be a new instance"""
        if self._view is not view:
            self._view = view

    def adjust_end(self):
        if self.repl.suppress_echo:
            v = self._view
            vsize = v.size()
            self._output_end = min(vsize, self._output_end)
            v.run_command("repl_erase_text", {"start": self._output_end, "end": vsize})
        else:
            self._output_end = self._view.size()

    def write(self, unistr):
        """Writes output from Repl into this view."""
        # remove color codes
        if self._filter_color_codes:
            unistr = re.sub(r"\033\[\d*(;\d*)?\w", "", unistr)
            unistr = re.sub(r".\x08", "", unistr)

        # string is assumed to be already correctly encoded
        self._view.run_command(
            "repl_insert_text",
            {"pos": self._output_end - self._prompt_size, "text": unistr},
        )
        self._output_end += len(unistr)
        self._view.show(self.input_region)

    def write_prompt(self, unistr):
        """Writes prompt from REPL into this view. Prompt is treated like
        regular output, except output is inserted before the prompt."""
        self._prompt_size = 0
        self.write(unistr)
        self._prompt_size = len(unistr)

    def handle_repl_output(self):
        """Returns new data from Repl and bool indicating if Repl is still
        working"""
        try:
            while True:
                packet = self._repl_reader.queue.get_nowait()
                if packet is None:
                    return False

                self.handle_repl_packet(packet)

        except queue.Empty:
            return True

    def handle_repl_packet(self, packet):
        if self.repl.apiv2:
            for opcode, data in packet:
                if opcode == "output":
                    self.write(data)
                elif opcode == "prompt":
                    self.write_prompt(data)
                elif opcode == "highlight":
                    a, b = data
                    regions = self._view.get_regions("sublimerepl")
                    regions.append(sublime.Region(a, b))
                    self._view.add_regions(
                        "sublimerepl",
                        regions,
                        "invalid",
                        "",
                        sublime.DRAW_EMPTY | sublime.DRAW_OUTLINED,
                    )
                else:
                    print("SublimeREPL-py: unknown REPL opcode: " + opcode)
        else:
            self.write(packet)

    def update_view_loop(self):
        is_still_working = self.handle_repl_output()
        if is_still_working:
            sublime.set_timeout(self.update_view_loop, 100)
        else:
            self.write(
                "\n***Repl Killed***\n"
                if self.repl._killed
                else "\n***Repl Closed***\n"
            )
            self._view.set_read_only(True)
            if sublime.load_settings(SETTINGS_FILE).get("view_auto_close"):
                window = self._view.window()
                if window is not None:
                    window.focus_view(self._view)
                    window.run_command("close")

    def push_history(self, command):
        self._history.push(command)
        self._history_match = None

    def ensure_history_match(self):
        user_input = self.user_input
        if self._history_match is not None:
            if user_input != self._history_match.current_command():
                # user did something! reset
                self._history_match = None
        if self._history_match is None:
            self._history_match = self._history.match(user_input)

    def replace_current_input(self, edit, cmd):
        if cmd:
            self._view.replace(edit, self.input_region, cmd)
            self._view.sel().clear()
            self._view.sel().add(sublime.Region(self._view.size()))

    @property
    def view(self):
        return self._view

    @property
    def input_region(self):
        return sublime.Region(self._output_end, self._view.size())

    @property
    def output_region(self):
        return sublime.Region(0, self._output_end - 2)

    @property
    def user_input(self):
        """Returns text entered by the user"""
        return self._view.substr(self.input_region)

    @property
    def delta(self):
        """Return a repl_view and number of characters from current selection
        to then begging of user_input (otherwise known as _output_end)"""
        return self._output_end - self._view.sel()[0].begin()

    def allow_deletion(self):
        # returns true if all selections falls in user input
        # and can be safetly deleted
        output_end = self._output_end
        for sel in self._view.sel():
            if sel.begin() == sel.end() and sel.begin() == output_end:
                # special case, when single selecion
                # is at the very beggining of prompt
                return False
            # i don' really know if end() is always after begin()
            if sel.begin() < output_end or sel.end() < output_end:
                return False
        return True


class ReplManager:
    def __init__(self):
        self.repl_views = {}

    def repl_view(self, view):
        repl_id = view.settings().get("repl_id")
        if repl_id not in self.repl_views:
            return None
        rv = self.repl_views[repl_id]
        rv.update_view(view)
        return rv

    def open(self, window, encoding, type, syntax=None, view_id=None, **kwds):
        repl_restart_args = {
            "encoding": encoding,
            "type": type,
            "syntax": syntax,
        }
        repl_restart_args.update(kwds)
        try:
            kwds = ReplManager.translate(window, kwds)
            encoding = ReplManager.translate(window, encoding)
            r = repls.Repl.subclass(type)(encoding, **kwds)
            found = None
            for view in window.views():
                if view.id() == view_id:
                    found = view
                    break
            view = found or window.new_file()

            rv = ReplView(view, r, syntax, repl_restart_args)
            rv.call_on_close.append(self._delete_repl)
            self.repl_views[r.id] = rv
            view.set_scratch(True)
            view.set_name("*REPL* [%s]" % (r.name(),))
            return rv
        except Exception as e:
            traceback.print_exc()
            sublime.error_message(repr(e))

    def restart(self, view, edit):
        repl_restart_args = view.settings().get("repl_restart_args")
        if not repl_restart_args:
            sublime.message_dialog("No restart parameters found")
            return False
        rv = self.repl_view(view)
        if rv:
            if (
                rv.repl
                and rv.repl.is_alive()
                and not sublime.ok_cancel_dialog("Still running. Really restart?")
            ):
                return False
            rv.on_close()  # yes on_close, delete rv from

        view.insert(edit, view.size(), RESTART_MSG)
        repl_restart_args["view_id"] = view.id()
        self.open(view.window(), **repl_restart_args)
        return True

    def _delete_repl(self, repl_view):
        repl_id = repl_view.repl.id
        if repl_id not in self.repl_views:
            return
        del self.repl_views[repl_id]

    @staticmethod
    def translate(window, obj, subst=None):
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        if isinstance(obj, dict):
            return ReplManager._translate_dict(window, obj, subst)
        # if isinstance(obj, unicode_type):  # PY2
        #     return ReplManager._translate_string(window, obj, subst)
        if isinstance(obj, list):
            return ReplManager._translate_list(window, obj, subst)
        return obj

    @staticmethod
    def _subst_for_translate(window):
        """Return all available substitutions"""
        res = {
            "packages": sublime.packages_path(),
            "installed_packages": sublime.installed_packages_path(),
        }
        if window.folders():
            res["folder"] = window.folders()[0]
        res["editor"] = "subl -w"
        av = window.active_view()
        if av is None:
            return res
        filename = av.file_name()
        if not filename:
            return res
        filename = os.path.abspath(filename)
        res["file"] = filename
        res["file_path"] = os.path.dirname(filename)
        res["file_basename"] = os.path.basename(filename)
        if "folder" not in res:
            res["folder"] = res["file_path"]

        return res

    @staticmethod
    def _translate_string(window, string, subst=None):
        from string import Template

        if subst is None:
            subst = ReplManager._subst_for_translate(window)

        # # Older Python runtimes can choke on dict(unicode -> unicode) as
        # # **kwargs, so normalize keys to str when needed.
        # if PY2:
        #     subst = dict((str(key), val) for key, val in subst.items())

        return Template(string).safe_substitute(**subst)

    @staticmethod
    def _translate_list(window, list, subst=None):
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        return [ReplManager.translate(window, x, subst) for x in list]

    @staticmethod
    def _translate_dict(window, dictionary, subst=None):
        if subst is None:
            subst = ReplManager._subst_for_translate(window)
        for k, v in list(dictionary.items()):
            dictionary[k] = ReplManager.translate(window, v, subst)
        return dictionary


manager = ReplManager()

# Window Commands #########################################


# Opens a new REPL
class ReplOpenCommand(sublime_plugin.WindowCommand):
    def run(self, encoding, type, syntax=None, view_id=None, **kwds):
        manager.open(self.window, encoding, type, syntax, view_id, **kwds)


class ReplRestartCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        manager.restart(self.view, edit)

    def is_visible(self):
        if not self.view:
            return False
        return bool(self.view.settings().get("repl_restart_args", None))

    def is_enabled(self):
        return self.is_visible()


# REPL Comands ############################################


# Submits the Command to the REPL
class ReplEnterCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.enter()


class ReplClearCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.clear(edit)


# Resets Repl Command Line
class ReplEscapeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.escape(edit)


class ReplBackspaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_backspace()


class ReplCtrlBackspaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_ctrl_backspace()


class ReplLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_left()


class ReplShiftLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_shift_left()


class ReplHomeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_home()


class ReplShiftHomeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.on_shift_home()


class ReplViewPreviousCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.previous_command(edit)


class ReplViewNextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        rv = manager.repl_view(self.view)
        if rv:
            rv.next_command(edit)


class SublimeReplListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        rv = manager.repl_view(view)
        if rv:
            rv.on_selection_modified()

    def on_close(self, view):
        rv = manager.repl_view(view)
        if rv:
            rv.on_close()

    def on_text_command(self, view, command_name, args):
        rv = manager.repl_view(view)
        if not rv:
            return None

        if command_name == "left_delete":
            # stop backspace on ST3 w/o breaking brackets
            if not rv.allow_deletion():
                return "repl_pass", {}

        if command_name == "delete_word" and not args.get("forward"):
            # stop ctrl+backspace on ST3 w/o breaking brackets
            if not rv.allow_deletion():
                return "repl_pass", {}

        return None
