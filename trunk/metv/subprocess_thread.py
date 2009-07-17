#!/usr/bin/env python

import async_subprocess as subprocess
import threading

class SubprocessThread:
    PROCESS_READ_INTERVAL = 0.5 # suck on the pipe every half second

    def __init__(self):
        self._process = None
        self._process_timer = None

    def _on_progress(self):
        """ Called after every PROCESS_READ_INTERVAL. """
        raise Exception("SubprocessThread._on_progress must be overridden.")

    def _process_line(self, line):
        """ Called whenever a line is received. """
        raise Exception("SubprocessThread._process_line must be overridden.")
                        
    def _on_finished(self):
        """ Called when the process exits. """
        raise Exception("SubprocessThread._on_finished must be overridden.")

    def start(self, cmd):
        self.cancel()
        self._cmd = cmd
        self._process_data = ""
        self.download_chunks = []
        self.error_message = None

        try:
            self._process = subprocess.Popen(cmd, shell=True, 
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)

        except OSError, inst:
            self.error_message = ("Could not execute %s (%s) "
                                   % (cmd[0], str(inst)))
            self._on_finished()

        self._start_process_timer()

    def cancel(self):
        if self._process_timer is not None:
            self._process_timer.cancel()
        if self._process is not None:
            self._process.kill()
               
    def _start_process_timer(self):
        if self._process_timer is not None:
            self._process_timer.cancel()
        self._process_timer = threading.Timer(self.PROCESS_READ_INTERVAL,
                                              self._on_process_timer)
        self._process_timer.start()
        
    def _on_process_timer(self, event=None):
        self.read()
        self._on_progress()

        if self._process is not None:
            self._start_process_timer()

    def read(self):
        # Start with any data left over from last time
        data = self._process_data
        # Receive any new chunks of data
        chunk = self._process.recv()
        while chunk is not None and chunk != "":
            self.download_chunks.append(chunk)
            data = data + chunk
            chunk = self._process.recv()

        # Split at \n's and \r's
        lines = data.split("\n")
        items = []
        for line in lines:
            items += line.split("\r")

        # Process each item
        while len(items) > 1:
            self._process_line(items.pop(0).strip())

        # Remember any left over data
        self._process_data = items[0]

        exitcode = self._process.poll()
        if exitcode is not None:
            if exitcode != 0:
                self.error_message = ("%s returned exit code %d" 
                                       % (self._cmd[0], exitcode))
            self._on_finished()
            self._process = None
                        

            
