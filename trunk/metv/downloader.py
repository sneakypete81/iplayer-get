#!/usr/bin/env python

import os
import async_subprocess as subprocess
import threading

class Downloader:
    DOWNLOAD_PENDING = 0
    DOWNLOAD_RUNNING = 1
    DOWNLOAD_COMPLETE = 2

    PROCESS_READ_INTERVAL = 0.5 # suck on the pipe every half second

    def __init__(self, settings):
        self.episodes = []
        self.settings = settings
        self.channel_download_counts = {}

        self._processes = []
        self._process_timer = None

    def add_episode(self, episode):
        self.episodes.append(episode)
        episode.download_state = self.DOWNLOAD_PENDING
        episode.download_error = False
        episode.download_message = None
        self._check_downloads()

    def _check_downloads(self):
        # Are we downloading enough already?
        if len(self._processes) >= self.settings.config.total_simultaneous_downloads:
            return
        for episode in [episode for episode in self.episodes 
                        if episode.download_state == self.DOWNLOAD_PENDING]:
            # Are we downloading enough from this channel already?
            if episode.type in self.channel_download_counts:
                if (self.channel_download_counts[episode.type] >=
                    self.settings.get_channel_settings(episode.type).simultaneous_downloads):
                    return
            self._download_start(episode)
                
    def _download_start(self, episode):
        episode.download_state = self.DOWNLOAD_RUNNING
        print("Downloading episode %s..." % episode.pid)
        cmd = ("get_iplayer " +
               "--force-download " +
               "--vmode=iphone " +
               "--vmode=flashvhigh,flashhigh,iphone,flashnormal " +
               "--file-prefix \"<name> <pid> <episode>\" " +
               "--output %s " % self.settings.config.download_dir +
               "--pid %s" % episode.pid)

        try:
            process = subprocess.Popen(cmd, shell=True, 
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            self._processes.append((episode, process))

        except OSError, inst:
            self._on_process_error(episode, "Could not execute get_iplayer " +
                                   "(%s)" % str(inst))
            raise

        episode._process_data = ""
        self._start_process_timer()
        print "Started download of %s" % episode.pid

    def _start_process_timer(self):
        if self._process_timer is not None:
            self._process_timer.cancel()
        self._process_timer = threading.Timer(self.PROCESS_READ_INTERVAL,
                                                 self._on_process_timer)
        self._process_timer.start()
        
    def _on_process_timer(self, event=None):
        for (episode, process) in self._processes:
            self.read_episode(episode, process)

        if len(self._processes) > 0:
            self._start_process_timer()

    def read_episode(self, episode, process):
        data = episode._process_data
        chunk = process.recv()
        while chunk is not None and chunk != "":
            data = data + chunk
            chunk = process.recv()

        # Split at \n's and \r's
        lines = data.split("\n")
        items = []
        for line in lines:
            items += line.split("\r")

        while len(items) > 1:
            self._process_line(episode, items.pop(0).strip())
        episode._process_data = items[0]

        exitcode = process.poll()
        if exitcode is not None:
            if exitcode == 0:
                self._on_process_ended(episode)
            else:
                self._on_process_error("iplayer-get returned exit code %d" % exitcode)

            self._processes.remove((episode, process))
            
    def _process_line(self, episode, line):
#        self.log.write("get-iplayer : %s" % line)
        if line.startswith("ERROR:"):
            error_message = line[6:].strip()
            print error_message
            episode.download_error = True
            episode.download_message = error_message
        if not self._process_rtmpdump_line(episode, line):
            self._process_iphone_line(episode, line)

    def _process_iphone_line(self, episode, line):
        try:
            (downloaded, line) = line.split("/")
            line = line.strip()
            (size, line) = line.split(" ", 1)
            line = line.strip()
            (rate, line) = line.split(" ", 1)
            line = line.strip()
            (percent, line) = line.split("%,")
            line = line.strip()
            (remaining_time, line) = line.split("remaining")

            episode.download_message = "Downloading %s / %s (%s%%) %skbps, %s remaining" \
                % (downloaded.strip(),
                   size.strip(),
                   percent.strip(),
                   rate.strip(),
                   remaining_time.strip())
            return True
        except ValueError, msg:
            # Couldn't understand the line - ignore
            return False

    def _process_rtmpdump_line(self, episode, line):
        try:
            (downloaded, line) = line.split(" KB (")
            line = line.strip()
            (percent, line) = line.split("%)")

            try:
                kb = int(float(downloaded))
                if kb < 1024:
                    downloaded = "%d KB" % kb
                else:
                    downloaded = "%d MB" % (kb/1024)
            except ValueError, inst:
                downloaded = downloaded + " KB"
            
            episode.download_message = "Downloading %s (%s%%)" \
                % (downloaded.strip(), percent.strip())
            return True

        except ValueError, msg:
            # Couldn't understand the line - ignore
            return False
            
    def _on_process_ended(self, episode):
        print "get-iplayer process ended: %s" % episode.pid
        episode.download_state = self.DOWNLOAD_COMPLETE
        episode.download_message = "Downloaded"

        if episode.error:
            self.SetStringItem(self.current_item, self.COL_STATUS, "Error: %s" %
                               episode.error_message)
        else:
            self.iplayer.mark_as_downloaded(episode)
            
    def _on_process_error(self, episode, message):
        episode.download_error = True
        episode.download_state = self.DOWNLOAD_COMPLETE
        episode.download_message = message
        print message