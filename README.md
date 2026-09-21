SublimeREPL-py Code Map
=======================

This package keeps only the Python-specific REPL path that starts in `project_venv_repl.py`, opens a `repl_open` window command from `sublimerepl.py`, and runs a `SubprocessRepl` backend from `repls/subprocess_repl.py`.

File: `__init__.py`
-------------------

This file is empty and defines no classes or methods.

File: `project_venv_repl.py`
----------------------------

### `ProjectVenvReplCommand`

Sublime Text text command that is invoked by the command palette and menu entries. It is the entry point for the package's remaining runtime flow.

#### `run(self, edit, interactive=False, name="python")`

Saves dirty file-backed views in the current window, resolves the interpreter with `get_venv_python`, builds either a file-running command or an interactive command, and forwards the launch request to `repl_open`. This is the start of the call graph for both supported workflows.

#### `get_venv_python(self, start_path)`

Walks upward from the current file and returns the first executable `.venv/bin/python` it finds. If no project-local interpreter is available, it falls back to `/usr/bin/python3`.

#### `repl_open(self, cmd_list, name, file_name)`

Dispatches Sublime Text's `repl_open` window command with the encoding, backend type, command line, working directory, syntax, and external identifier. This hands control to `ReplOpenCommand.run` in `sublimerepl.py`.

File: `repls/__init__.py`
-------------------------

This file re-exports the classes from `repls/repl.py` and `repls/subprocess_repl.py`. It defines no classes or methods of its own, but it lets `sublimerepl.py` access `repls.Repl` and `repls.SubprocessRepl` through a single package import.

File: `repls/repl.py`
---------------------

### `NoReplError`

Raised when `Repl.subclass` cannot find a backend for the requested REPL type.

### `Repl`

Abstract base class for all REPL backends. `ReplManager.open` uses `Repl.subclass` to resolve the backend type requested by `project_venv_repl.py`.

#### `subclass(cls, type)`

Searches the `Repl` subclass tree and returns the class whose `TYPE` matches the requested backend name. `ReplManager.open` uses this to resolve `"subprocess"` into `SubprocessRepl`.

#### `__init__(self, encoding, external_id=None, cmd_postfix="\n", suppress_echo=False, additional_scopes=None, apiv2=False)`

Initializes the shared backend state: an internal ID, text encoder/decoder, restart metadata, command postfix handling, and API mode flags. `SubprocessRepl.__init__` delegates here before starting the subprocess.

#### `allow_restarts(self)`

Returns `True` for this backend, which allows `ReplView` to persist restart arguments and `ReplRestartCommand` to stay available.

#### `close(self)`

Closes the backend by calling `kill` when the backend is still alive. `ReplView.on_close` uses this during REPL shutdown.

#### `name(self)`

Abstract backend naming hook used by `ReplManager.open` when naming the REPL view.

#### `is_alive(self)`

Abstract liveness hook used by `close`, restart handling, and the output polling loop.

#### `write_bytes(self, bytes)`

Abstract low-level output method that a concrete backend must implement.

#### `read_bytes(self)`

Abstract low-level input method that a concrete backend must implement.

#### `kill(self)`

Abstract process-termination hook used by `close` and restart handling.

#### `write(self, command)`

Encodes a Unicode command and forwards it to `write_bytes`. `ReplView.enter` uses this to send user input to the backend.

#### `reset_decoder(self)`

Reinitializes the incremental decoder after decode failures. `read` uses this to recover from malformed byte sequences.

#### `read(self)`

Reads backend bytes, decodes them into text, and returns the next output chunk. `ReplReader.run` calls this in a background thread and pushes the results into the UI queue.

File: `repls/subprocess_repl.py`
--------------------------------

### `Unsupported`

Exception used when a requested command line is explicitly marked unsupported.

#### `__init__(self, msgs)`

Stores the unsupported-command explanation lines.

#### `__repr__(self)`

Formats the stored explanation lines for the error dialog shown by `ReplManager.open`.

### `SubprocessRepl`

Concrete `Repl` backend for local subprocess execution. This is the only runtime backend that remains in the package, and `ReplManager.open` constructs it for every `project_venv_repl` launch.

#### `__init__(self, encoding, cmd=None, env=None, cwd=None, extend_env=None, soft_quit="", **kwds)`

Loads settings, resolves the environment, starts the subprocess, and makes its stdout non-blocking. This backend instance is then wrapped by `ReplView`.

#### `cmd(self, cmd, env)`

Returns the command sequence to execute. In this trimmed fork it is a direct passthrough of the list assembled in `ProjectVenvReplCommand.run`.

#### `cwd(self, cwd, settings)`

Returns the requested working directory when it exists, otherwise `None`. `__init__` uses it when starting the subprocess.

#### `getenv(self, settings)`

Builds the base environment, optionally by running the configured login-shell probe. `env` falls back to this when no explicit environment is supplied.

#### `env(self, env, extend_env, settings)`

Merges the discovered environment with package-level and call-level overrides, then encodes the environment into the byte-oriented form expected by the base class encoder logic.

#### `interpolate_extend_env(self, env, extend_env)`

Interpolates string templates inside environment override values. `env` uses it for both default and call-specific environment extensions.

#### `name(self)`

Returns the external ID when present, otherwise a readable name derived from the subprocess command. `ReplManager.open` uses this when naming the view.

#### `is_alive(self)`

Reports whether the subprocess is still running. This is used by shutdown, restart, and output-loop logic.

#### `read_bytes(self)`

Blocks until subprocess stdout becomes readable, then returns the next chunk of bytes. `Repl.read` consumes these bytes and turns them into UI text.

#### `write_bytes(self, bytes)`

Writes encoded input to subprocess stdin. `Repl.write` reaches this method after encoding the command text.

#### `kill(self)`

Marks the backend as killed, sends any configured soft-quit text, and forcibly terminates the process group. `Repl.close` and restart handling use this for shutdown.

File: `sublimerepl.py`
----------------------

### `ReplInsertTextCommand`

Helper text command used internally by `ReplView.write` to insert REPL output into the view even when the view is usually read-only.

#### `run(self, edit, pos, text)`

Temporarily makes the view writable and inserts text at the requested position.

### `ReplEraseTextCommand`

Helper text command used internally by `ReplView.adjust_end` when echo suppression requires erasing stale text.

#### `run(self, edit, start, end)`

Temporarily makes the view writable and erases the requested region.

### `ReplPass`

No-op text command returned by the event listener to block unsafe deletion commands in REPL output.

#### `run(self, edit)`

Does nothing; it exists only as a safe replacement command.

### `ReplReader`

Background thread that continuously pulls decoded output from a `Repl` backend and queues it for the UI layer.

#### `__init__(self, repl)`

Stores the backend, marks the thread as daemonized, and creates the output queue.

#### `run(self)`

Reads output chunks from the backend until it closes and enqueues each chunk for `ReplView.handle_repl_output`.

### `HistoryMatchList`

Cursor object for navigating through history entries that match the current input prefix.

#### `__init__(self, command_prefix, commands)`

Stores the prefix, the matching commands, and an initial cursor positioned after the last entry.

#### `current_command(self)`

Returns the command at the current cursor position, or an empty string when no history entries match.

#### `prev_command(self)`

Moves backward through the matching history list and returns the selected command.

#### `next_command(self)`

Moves forward through the matching history list and returns the selected command.

### `History`

Abstract command-history base class used by `ReplView`.

#### `__init__(self)`

Initializes the last-command guard used to avoid pushing duplicate adjacent history entries.

#### `push(self, command)`

Normalizes a command, skips empty or duplicate entries, and forwards accepted entries to `append`.

#### `append(self, cmd)`

Abstract storage hook implemented by `MemHistory`.

#### `match(self, command_prefix)`

Abstract lookup hook implemented by `MemHistory`.

### `MemHistory`

In-memory history implementation used by every `ReplView`.

#### `__init__(self)`

Initializes the base history state and the in-memory command stack.

#### `append(self, cmd)`

Adds a command to the in-memory stack.

#### `match(self, command_prefix)`

Builds a `HistoryMatchList` containing commands that start with the current input prefix.

### `ReplView`

UI/controller object that connects a Sublime Text view to a running `Repl` backend. `ReplManager.open` creates it immediately after constructing a backend.

#### `__init__(self, view, repl, syntax, repl_restart_args)`

Stores the backend and view, applies syntax and settings, starts a `ReplReader`, optionally moves the view to another group, and schedules the periodic output polling loop.

#### `on_backspace(self)`

Allows backspace to operate only when the caret is inside editable input.

#### `on_ctrl_backspace(self)`

Allows backward word deletion only when the caret is inside editable input.

#### `on_left(self)`

Prevents the caret from moving left into protected output.

#### `on_shift_left(self)`

Prevents shift-left selection from extending into protected output.

#### `on_home(self)`

Moves to the start of the editable input area instead of the start of protected output.

#### `on_shift_home(self)`

Extends selection to the start of the editable input area without entering protected output.

#### `on_selection_modified(self)`

Toggles read-only state depending on whether the selection enters protected output.

#### `on_close(self)`

Closes the backend and runs registered close callbacks. `SublimeReplListener.on_close` calls this when the view is closed.

#### `clear(self, edit)`

Erases both the current input and accumulated output. `ReplClearCommand.run` delegates here.

#### `escape(self, edit)`

Clears only the current input region. `ReplEscapeCommand.run` delegates here.

#### `enter(self)`

Captures the current input, stores it in history, appends the command postfix to the view, and writes the command to the backend. `ReplEnterCommand.run` delegates here.

#### `previous_command(self, edit)`

Replaces current input with the previous history match. `ReplViewPreviousCommand.run` delegates here.

#### `next_command(self, edit)`

Replaces current input with the next history match. `ReplViewNextCommand.run` delegates here.

#### `update_view(self, view)`

Refreshes the stored view object when Sublime recreates the underlying view instance.

#### `adjust_end(self)`

Advances the boundary between output and input, optionally erasing echoed input when the backend suppresses echo.

#### `write(self, unistr)`

Inserts backend output into the view, filtering terminal color codes when configured.

#### `write_prompt(self, unistr)`

Writes prompt text and records its size so later output can be inserted before the prompt.

#### `handle_repl_output(self)`

Drains queued output from `ReplReader` and returns whether the backend is still active.

#### `handle_repl_packet(self, packet)`

Routes either plain text output or API-v2 opcode packets into the correct rendering path.

#### `update_view_loop(self)`

Schedules recurring output polling while the backend is alive, and marks or closes the view when the backend exits.

#### `push_history(self, command)`

Stores a submitted command and clears any active history-match cursor.

#### `ensure_history_match(self)`

Builds or refreshes the current `HistoryMatchList` for prefix-based history navigation.

#### `replace_current_input(self, edit, cmd)`

Overwrites the current input region with a history entry and moves the caret to the end.

#### `view(self)`

Returns the underlying Sublime Text view.

#### `input_region(self)`

Returns the editable input region at the end of the view.

#### `output_region(self)`

Returns the protected output region before the current input.

#### `user_input(self)`

Returns the current editable input text.

#### `delta(self)`

Returns the distance between the caret and the beginning of the editable input region.

#### `allow_deletion(self)`

Checks whether every current selection stays inside editable input, allowing deletion commands to proceed.

### `ReplManager`

Registry and factory for live REPL views. `ReplOpenCommand` delegates opening here, and most text commands ask it to resolve the current `ReplView`.

#### `__init__(self)`

Initializes the in-memory mapping from backend IDs to `ReplView` instances.

#### `repl_view(self, view)`

Returns the `ReplView` associated with a Sublime view and refreshes the stored view object when needed.

#### `open(self, window, encoding, type, syntax=None, view_id=None, **kwds)`

Translates launch arguments, resolves the backend class, creates or reuses the target view, builds a `ReplView`, stores it in the manager, and names the buffer. This is the main bridge from `ProjectVenvReplCommand.repl_open` into the REPL UI/backend stack.

#### `restart(self, view, edit)`

Closes an existing REPL, appends a restart marker, and reopens the same view with the saved launch arguments. `ReplRestartCommand.run` delegates here.

#### `_delete_repl(self, repl_view)`

Removes a closed `ReplView` from the manager's registry.

#### `translate(window, obj, subst=None)`

Dispatches launch-argument translation by object type so strings, lists, and dictionaries can all use the same variable-substitution mechanism.

#### `_subst_for_translate(window)`

Builds the `${packages}`, `${file}`, `${folder}`, and related substitutions used when expanding launch arguments.

#### `_translate_string(window, string, subst=None)`

Applies template substitution to a single string.

#### `_translate_list(window, list, subst=None)`

Applies recursive translation to each element of a list.

#### `_translate_dict(window, dictionary, subst=None)`

Applies recursive translation to each value in a dictionary.

### `ReplOpenCommand`

Window command named `repl_open`, which is the command dispatched by `ProjectVenvReplCommand.repl_open`.

#### `run(self, encoding, type, syntax=None, view_id=None, **kwds)`

Forwards the launch request to `ReplManager.open`.

### `ReplRestartCommand`

Text command that restarts the current REPL with its saved launch arguments.

#### `run(self, edit)`

Delegates restart handling to `ReplManager.restart`.

#### `is_visible(self)`

Shows the command only when the current view has restart metadata.

#### `is_enabled(self)`

Enables the command under the same condition as `is_visible`.

### `ReplEnterCommand`

Text command bound to Enter inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and submits its input through `ReplView.enter`.

### `ReplClearCommand`

Text command bound to `ctrl+l` inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and clears it through `ReplView.clear`.

### `ReplEscapeCommand`

Text command bound to Escape inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and clears only the current input through `ReplView.escape`.

### `ReplBackspaceCommand`

Text command used for backspace handling inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.on_backspace`.

### `ReplCtrlBackspaceCommand`

Text command used for backward word deletion inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.on_ctrl_backspace`.

### `ReplLeftCommand`

Text command used for left-arrow navigation inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.on_left`.

### `ReplShiftLeftCommand`

Text command used for shift-left selection inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.on_shift_left`.

### `ReplHomeCommand`

Text command used for Home navigation inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.on_home`.

### `ReplShiftHomeCommand`

Text command used for shift-home selection inside REPL views.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.on_shift_home`.

### `ReplViewPreviousCommand`

Text command used for backward history navigation.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.previous_command`.

### `ReplViewNextCommand`

Text command used for forward history navigation.

#### `run(self, edit)`

Looks up the current `ReplView` and delegates to `ReplView.next_command`.

### `SublimeReplListener`

Event listener that keeps REPL views protected and synchronized with their backend lifecycle.

#### `on_selection_modified(self, view)`

Delegates selection-state updates to `ReplView.on_selection_modified`.

#### `on_close(self, view)`

Delegates REPL shutdown to `ReplView.on_close`.

#### `on_text_command(self, view, command_name, args)`

Intercepts unsafe delete commands in protected output and replaces them with `repl_pass`.
