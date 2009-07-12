#!/usr/bin/env python

import os
import async_subprocess as subprocess
import threading
from wx.lib.pubsub import Publisher
from wx import CallAfter

import programme
import settings
import downloader
import streamer

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
#                             Channel("Channel 4", "ch4", self.settings),
#                             Channel("Five", "five", self.settings),
#                             Channel("BBC Podcasts", "podcast", self.settings),
                             Channel("BBC Radio", "radio", self.settings),
#                             Channel("Hulu", "hulu", self.settings),
                             ])
        self.downloader = downloader.Downloader(self.settings)
        self.streamer = streamer.Streamer(self.settings)

    def shutdown(self):
        """ Make sure all subprocesses get stopped,
            and all settings are saved."""
        self.settings.write()
        for channel in self:
            channel.cancel_refresh()
        self.downloader.cancel_all()
        self.streamer.cancel()

    def refresh_all(self):
        for channel in self:
            channel.refresh()

class Channel():
    PROCESS_READ_INTERVAL = 0.5 # suck on the pipe every half second

    def __init__(self, title, code, settings):
        self.title = title
        self.code = code
        self.all_programmes = {}
        self.subscribed_programmes = {}
        self.is_refreshing = False
        self.error_message = None
        self.download_chunks = []

        self._cache_filename = os.path.join(PROFILE_DIR, "%s.cache" % code)

        self.settings = settings
        self.channel_settings = settings.get_channel_settings(title)

        self._process = None
        self._process_timer = None

    def refresh(self):
        """ Start get_iplayer process to refresh the cache """
        self.error_message = None
        self.is_refreshing = True
        
        # Temp to disable cache refresh
#         self._on_process_ended()
#         return

        cmd = (self.settings.config.get_iplayer_cmd + " " +
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
#        print chunk
        while chunk is not None and chunk != "":
            self.download_chunks.append(chunk)
            data = data + chunk
            chunk = self._process.recv()
#            print chunk
  
       # See if we're finished
        exitcode = self._process.poll()
        if exitcode is None:
            self._start_process_timer()
        else:
            if exitcode == 0:
                self._on_process_ended()
            else:
                self._on_process_error("get_iplayer returned exit code %d" % exitcode)
                   
    def _on_process_ended(self):
        """ iplayer_get process has finished """
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

                if episode.pid in self.channel_settings.downloaded_episodes:
                    episode.downloaded = True
                else:
                    episode.downloaded = False

                if episode.pid in self.channel_settings.ignored_episodes:
                    episode.ignored = True
                else:
                    episode.ignored = False

                # Create a new programme if necessary
                if episode.name in self.all_programmes:
                    prog = self.all_programmes[episode.name]
                else:
                    prog = programme.Programme(channel_obj=self, 
                                               name=episode.name)
                    self.all_programmes[episode.name] = prog

                prog.episodes.append(episode)

                # Check if programme is unsubscribed
                if episode.name in self.channel_settings.unsubscribed_programmes:
                    continue
                if (self.channel_settings.require_subscription and 
                    episode.name not in self.channel_settings.subscribed_programmes):
                    continue

                self.subscribed_programmes[episode.name] = prog



    #         self.log.write("Cache parsing complete.")
        except Exception, inst:
            self._on_process_error(str(inst))

    def unsubscribe(self, programme):
        if programme.name in self.subscribed_programmes:
            del self.subscribed_programmes[programme.name]

            if programme.name not in self.channel_settings.unsubscribed_programmes:
                self.channel_settings.unsubscribed_programmes.append(programme.name)
            if programme.name in self.channel_settings.subscribed_programmes:
                self.channel_settings.subscribed_programmes.remove(programme.name)

    def mark_downloaded(self, episode):
        self.channel_settings.downloaded_episodes.append(episode.pid)
        episode.downloaded = True

    def ignore(self, episode):
        """ Toggle ignore status """
        if episode.pid in self.channel_settings.ignored_episodes:
            self.channel_settings.ignored_episodes.remove(episode.pid)
            episode.ignored = False
        else:
            self.channel_settings.ignored_episodes.append(episode.pid)
            episode.ignored = True
