#!/usr/bin/env python
import pickle
import os
import sys

SETTINGS_FILE = os.path.expanduser("~/.idiotbox")

class Settings():
    def __init__(self):
        self.config = ConfigSettings()
        self._channels = {}
        self.read()

    def read(self):
        try:
            f = open(SETTINGS_FILE, 'rb')
            self.config.__dict__.update(pickle.load(f).__dict__)

            saved_channels = pickle.load(f)
            for title, saved_channel in saved_channels.items():
                channel = self.get_channel_settings(title)
                channel.__dict__.update(saved_channel.__dict__)
                

        except IOError, inst:#Exception, inst:
            print "Could not read settings: %s" % str(inst)
            pass

    def write(self):
        f = open(SETTINGS_FILE, 'wb')
        pickle.dump(self.config, f, pickle.HIGHEST_PROTOCOL)
        pickle.dump(self._channels, f, pickle.HIGHEST_PROTOCOL)

    def get_channel_settings(self, title):
        if title not in self._channels:
            self._channels[title] = ChannelSettings()
        return self._channels[title]

class ConfigSettings():
    def __init__(self):
        if sys.platform == "win32":
            self.get_iplayer_cmd = ("c:\Progra~1\get_iplayer\perl.exe " +
                                    "c:\Progra~1\get_iplayer\get_iplayer.pl")
        else:
            self.get_iplayer_cmd = "get_iplayer"

        self.download_dir = "."
        self.total_simultaneous_downloads = 3

class ChannelSettings():
    def __init__(self):
        self.subscribed_programmes = []
        self.unsubscribed_programmes = []
        self.require_subscription = False
        self.simultaneous_downloads = 1

        self.downloaded_episodes = []
