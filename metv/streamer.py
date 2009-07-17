#!/usr/bin/env python

from subprocess_thread import SubprocessThread
from wx.lib.pubsub import Publisher
from wx import CallAfter

class Streamer(SubprocessThread):
    TOPIC_STREAMING_PROGRESS = "streaming.progress"
    TOPIC_STREAMING_COMPLETE = "streaming.complete"
    TOPIC_STREAMING_ERROR = "streaming.complete"

    def __init__(self, settings):
        self._settings = settings
        SubprocessThread.__init__(self)

    def stream(self, episode):
        self.cancel()
        self._episode = episode

        cmd = ("get_iplayer " +
               "--vmode=flashhd,flashvhigh,flashhigh,flashnormal " +
               "--stream " +
               "--player \"vlc file:///dev/stdin\" " +
               "--pid %s" % episode.pid)

        self.start(cmd)

    def _on_progress(self):
        # use CallAfter to switch back to the main GUI thread
        CallAfter(Publisher().sendMessage, 
                  topic=self.TOPIC_STREAMING_PROGRESS)

    def _process_line(self, line):
        pass
                        
    def _on_finished(self):

        if self.error_message is None:
            self._episode.download_message = "Finished"
            topic = self.TOPIC_STREAMING_COMPLETE
        else:
            self._episode.download_message = ("Error: %s" 
                                              % self.error_message)
            topic = self.TOPIC_STREAMING_ERROR

        # use CallAfter to switch back to the main GUI thread
        CallAfter(Publisher().sendMessage, 
                  topic=topic,
                  data=self._episode)

            
