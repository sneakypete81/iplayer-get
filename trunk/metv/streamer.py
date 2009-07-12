#!/usr/bin/env python

import async_subprocess as subprocess
import threading
from wx.lib.pubsub import Publisher
from wx import CallAfter

class Streamer:
    PROCESS_READ_INTERVAL = 0.5 # suck on the pipe every half second

    TOPIC_STREAMING_PROGRESS = "streaming.progress"
    TOPIC_STREAMING_COMPLETE = "streaming.complete"
    TOPIC_STREAMING_ERROR = "streaming.complete"

    def __init__(self, settings):
        self.settings = settings

        self._process = None
        self._process_timer = None

    def stream(self, episode):
        self.cancel()
        self._episode = episode
        episode.download_chunks = []
        episode.download_message = ""
        episode.error_message = None

        cmd = ("get_iplayer " +
               "--vmode=flashhd,flashvhigh,flashhigh,flashnormal " +
               "--stream " +
               "--player \"vlc file:///dev/stdin\" " +
               "--pid %s" % episode.pid)

        try:
            self._process = subprocess.Popen(cmd, shell=True, 
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)

        except OSError, inst:
            episode.error_message = ("Could not execute get_iplayer " +
                                     "(%s)" % str(inst))
            self._on_process_ended(episode)

        episode._process_data = ""
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
        self.read_episode(self._episode, self._process)

        # use CallAfter to switch back to the main GUI thread
        CallAfter(Publisher().sendMessage, 
                  topic=self.TOPIC_STREAMING_PROGRESS)

        if self._process is not None:
            self._start_process_timer()

    def read_episode(self, episode, process):
        data = episode._process_data
        chunk = process.recv()
        while chunk is not None and chunk != "":
            episode.download_chunks.append(chunk)
            data = data + chunk
            chunk = process.recv()
        # Split at \n's and \r's
        lines = data.split("\n")
        items = []
        for line in lines:
            items += line.split("\r")

#         while len(items) > 1:
#             self._process_line(episode, items.pop(0).strip())
        episode._process_data = items[0]

        exitcode = process.poll()
        if exitcode is not None:
            if exitcode != 0:
                episode.error_message = ("iplayer-get returned exit code %d" 
                                         % exitcode)
            self._on_process_ended(episode)
            self._process = None
                        
    def _on_process_ended(self, episode):

        if episode.error_message is None:
            episode.download_message = "Finished"
            topic = self.TOPIC_STREAMING_COMPLETE
        else:
            episode.download_message = "Error: %s" % episode.error_message
            topic = self.TOPIC_STREAMING_ERROR

        # use CallAfter to switch back to the main GUI thread
        CallAfter(Publisher().sendMessage, 
                  topic=topic,
                  data=episode)

            
