#!/usr/bin/env python

import os
import async_subprocess as subprocess
import time
import threading
from wx.lib.pubsub import Publisher
from wx import CallAfter

import programme
import settings

if 'HOME' in os.environ:
    HOME_DIR = os.environ['HOME']
elif 'USERPROFILE' in os.environ:
    HOME_DIR = os.environ['USERPROFILE']
else:
    HOME_DIR = os.expanduser("~")
    
PROFILE_DIR = os.path.join(HOME_DIR, ".get_iplayer")

class Channels(list):
    TOPIC_REFRESH_PROGRESS = "refresh.progress"
    TOPIC_REFRESH_COMPLETE = "refresh.complete"
    TOPIC_REFRESH_ERROR    = "refresh.error"

    def __init__(self):
        self.settings = settings.Settings()
        list.__init__(self, [Channel("BBC TV", "tv", self.settings),
                             Channel("ITV", "itv", self.settings),
                             Channel("Channel 4", "ch4", self.settings),
                             Channel("Five", "five", self.settings),
                             Channel("BBC Podcasts", "podcast", self.settings),
                             Channel("BBC Radio", "radio", self.settings),
#                             Channel("Hulu", "hulu", self.settings),
                             ])

    def __del__(self):
        """ Make sure all refresh subprocesses get stopped,
            and all settings are saved."""
        self.settings.write()
        for channel in self:
            channel.cancel_refresh()

    def refresh_all(self):
        for channel in self:
            channel.refresh()

class Channel():
    PROCESS_READ_INTERVAL = 0.5 # suck on the pipe every half second

    def __init__(self, title, code, settings):
        self.title = title
        self.code = code
        self.programmes = {}
        self.is_refreshing = False
        self.error_message = None

        self._cache_filename = os.path.join(PROFILE_DIR, "%s.cache" % code)

        self.settings = settings.get_channel_settings(title)
        
        self._process = None
        self._process_timer = None

    def refresh(self):
        """ Start get_iplayer process to refresh the cache """
        self.error_message = None
        self.is_refreshing = True

        
        # Temp to disable cache refresh
        self._on_process_ended()
        return


        cmd = ("get_iplayer " 
               "--refresh " + # Force update of cache
               "--nopurge " +  # Prevent old episode deletion prompt
               "--type=%s " % self.code)
        try:
            self._process = subprocess.Popen(cmd, shell=True, 
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)
        except OSError, inst:
            self._on_process_error("Could not start get_iplayer.")
            raise

        self._process_data = ""
        self._start_process_timer()
        print "Started refresh process: %s" % self.title

    def cancel_refresh(self):
        if self.is_refreshing:
            self._process.kill()
            self._process_timer.cancel()

    def _start_process_timer(self):
        if self._process_timer is not None:
            self._process_timer.cancel()
        self._process_timer = threading.Timer(self.PROCESS_READ_INTERVAL,
                                              self._on_process_timer)
        self._process_timer.start()


    def _on_process_timer(self, event=None):
        """ Read data from stdout/err """
        self._process_timer = None
        data = ""
        chunk = self._process.recv()
        while chunk is not None and chunk != "":
            data = data + chunk
            chunk = self._process.recv()
  
       # See if we're finished
        exitcode = self._process.poll()
        if exitcode is None:
            self._start_process_timer()
        else:
            if exitcode == 0:
                self._on_process_ended()
            else:
                self._on_process_error("iplayer-get returned exit code %d" % exitcode)
                   
    def _on_process_ended(self):
        """ iplayer_get process has finished """
        print "Refresh process finished: %s" % self.title
        # use CallAfter to switch back to the main GUI thread
        CallAfter(Publisher().sendMessage, 
                  topic=Channels.TOPIC_REFRESH_COMPLETE,
                  data=self)
        self.is_refreshing = False
        self._process = None

    def _on_process_error(self, message):
        """ iplayer_get process returned an error """
        # use CallAfter to switch back to the main GUI thread
        CallAfter(Publisher().sendMessage, 
                  topic=Channels.TOPIC_REFRESH_ERROR,
                  data=self)
        self.error_message = message
        self.is_refreshing = False
        self._process = None

    def parse_cache(self):
        try:
            f = open(self._cache_filename)
            # Parse the headings
            first_line = f.readline().strip()
            if first_line[0] != "#":
    #             self.log.write("Invalid cache file format.")
    #             self.log.write("First line was: '%s'" % first_line)
                raise ValueError("Invalid cache file format.")

            headings = first_line[1:].split("|")       
    #         self.log.write("Cache headings: %s" % str(headings))

            lines = f.readlines()
    #         self.log.write("Parsing %d lines from cache..." % len(lines))

            for line in lines:
                # Create an episode object
                episode = programme.Episode()
                episode.channel_obj = self

                split_line = line.split("|")
                for i,heading in enumerate(headings):
                    episode.__dict__[heading] = split_line[i]

                episode.name = unicode(episode.name, 'utf-8')
                if episode.type == "itv":
                    episode.pid = "itv:"+episode.pid
                if episode.type == "ch4":
                    episode.pid = "ch4:"+episode.pid
                if episode.type == "five":
                    episode.pid = "five:"+episode.pid

                # Ignore if programme is unsubscribed
                if episode.name in self.settings.unsubscribed_programmes:
                    continue
                if (self.settings.require_subscription and 
                    episode.name not in self.settings.subscribed_programmes):
                    continue

                if episode.pid in self.settings.downloaded_episodes:
                    episode.downloaded = True
                else:
                    episode.downloaded = False

                if episode.pid in self.settings.ignored_episodes:
                    episode.ignored = True
                else:
                    episode.ignored = False

                # Create a new programme if necessary
                if episode.name not in self.programmes:
                    self.programmes[episode.name] = \
                        programme.Programme(channel_obj=self, 
                                            name=episode.name)

                self.programmes[episode.name].episodes.append(episode)

    #         self.log.write("Cache parsing complete.")
        except Exception, inst:
            self._on_process_error(str(inst))

    def unsubscribe(self, programme):
        if programme.name in self.programmes:
            del self.programmes[programme.name]

            if programme.name not in self.settings.unsubscribed_programmes:
                self.settings.unsubscribed_programmes.append(programme.name)
            if programme.name in self.settings.subscribed_programmes:
                self.settings.subscribed_programmes.remove(programme.name)

    def download(self, episode):
        print "download %s" % episode.episode
        pass

    def ignore(self, episode):
        """ Toggle ignore status """
        if episode.pid in self.settings.ignored_episodes:
            self.settings.ignored_episodes.remove(episode.pid)
            episode.ignored = False
        else:
            self.settings.ignored_episodes.append(episode.pid)
            episode.ignored = True
