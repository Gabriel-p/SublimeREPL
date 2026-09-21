# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.
from __future__ import absolute_import, unicode_literals, print_function, division

import subprocess
import os
import sys
import signal
from .repl import Repl
from sublime import load_settings, error_message
from .autocomplete_server import AutocompleteServer

PY3 = sys.version_info[0] == 3

import fcntl
import select


class Unsupported(Exception):
    def __init__(self, msgs):
        super(Unsupported, self).__init__()
        self.msgs = msgs

    def __repr__(self):
        return "\n".join(self.msgs)

class SubprocessRepl(Repl):
    TYPE = "subprocess"

    def __init__(self, encoding, cmd=None, env=None, cwd=None, extend_env=None, soft_quit="", autocomplete_server=False, **kwds):
        super(SubprocessRepl, self).__init__(encoding, **kwds)
        settings = load_settings('SublimeREPL.sublime-settings')

        if cmd[0] == "[unsupported]":
            raise Unsupported(cmd[1:])

        self._autocomplete_server = None
        if autocomplete_server:
            self._autocomplete_server = AutocompleteServer(self, settings.get("autocomplete_server_ip"))
            self._autocomplete_server.start()

        env = self.env(env, extend_env, settings)
        env[b"SUBLIMEREPL_AC_PORT"] = str(self.autocomplete_server_port()).encode("utf-8")
        env[b"SUBLIMEREPL_AC_IP"] = settings.get("autocomplete_server_ip").encode("utf-8")

        if PY3:
            strings_env = {}
            for k, v in env.items():
                strings_env[k.decode("utf-8")] = v.decode("utf-8")
            env = strings_env

        self._cmd = self.cmd(cmd, env)
        self._soft_quit = soft_quit
        self._killed = False
        self.popen = subprocess.Popen(
                        self._cmd,
                        bufsize=1,
                        preexec_fn=os.setsid,
                        cwd=self.cwd(cwd, settings),
                        env=env,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE)

        flags = fcntl.fcntl(self.popen.stdout, fcntl.F_GETFL)
        fcntl.fcntl(self.popen.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def autocomplete_server_port(self):
        if not self._autocomplete_server:
            return None
        return self._autocomplete_server.port()

    def autocomplete_available(self):
        if not self._autocomplete_server:
            return False
        return self._autocomplete_server.connected()

    def autocomplete_completions(self, whole_line, pos_in_line, prefix, whole_prefix, locations):
        return self._autocomplete_server.complete(
            whole_line=whole_line,
            pos_in_line=pos_in_line,
            prefix=prefix,
            whole_prefix=whole_prefix,
            locations=locations,
        )

    def cmd(self, cmd, env):
        return cmd

    def cwd(self, cwd, settings):
        if cwd and os.path.exists(cwd):
            return cwd
        return None

    def getenv(self, settings):
        """Tries to get most appropriate environment from the login shell."""

        getenv_command = settings.get("getenv_command")
        if getenv_command:
            try:
                output = subprocess.check_output(getenv_command)
                lines = output.decode("utf-8", errors="replace").splitlines()
                env = dict(line.split('=', 1)  for line in lines)
                return env
            except:
                import traceback
                traceback.print_exc()
                error_message(
                    "SublimeREPL: obtaining sane environment failed in getenv()\n"
                    "Check console and 'getenv_command' setting \n"
                    "WARN: Falling back to SublimeText environment")

        return os.environ.copy()

    def env(self, env, extend_env, settings):
        updated_env = env if env else self.getenv(settings)
        default_extend_env = settings.get("default_extend_env")
        if default_extend_env:
            updated_env.update(self.interpolate_extend_env(updated_env, default_extend_env))
        if extend_env:
            updated_env.update(self.interpolate_extend_env(updated_env, extend_env))

        bytes_env = {}
        for k, v in list(updated_env.items()):
            try:
                enc_k = self.encoder(str(k))[0]
                enc_v = self.encoder(str(v))[0]
            except UnicodeDecodeError:
                continue #f*** it, we'll do it live
            else:
                bytes_env[enc_k] = enc_v
        return bytes_env

    def interpolate_extend_env(self, env, extend_env):
        """Interpolates (subst) values in extend_env.
           Mostly for path manipulation"""
        new_env = {}
        for key, val in list(extend_env.items()):
            new_env[key] = str(val).format(**env)
        return new_env

    def name(self):
        if self.external_id:
            return self.external_id
        if isinstance(self._cmd, str):
            return self._cmd
        return " ".join([str(x) for x in self._cmd])

    def is_alive(self):
        return self.popen.poll() is None

    def read_bytes(self):
        out = self.popen.stdout
        while True:
            i, _, _ = select.select([out], [], [])
            if i:
                return out.read(4096)



    def write_bytes(self, bytes):
        si = self.popen.stdin
        si.write(bytes)
        si.flush()

    def kill(self):
        self._killed = True
        self.write(self._soft_quit)
        try:
            os.killpg(self.popen.pid, signal.SIGKILL)
        except OSError:
            pass
        self.popen.kill()

    def available_signals(self):
        signals = {}
        for k, v in list(signal.__dict__.items()):
            if not k.startswith("SIG"):
                continue
            signals[k] = v
        return signals

    def send_signal(self, sig):
        if sig == signal.SIGTERM:
            self._killed = True
        if self.is_alive():
            os.killpg(self.popen.pid, sig)
