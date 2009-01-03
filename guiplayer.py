#!/usr/bin/env python

# Todo:
#  * Download manager
#  * Thumbnails (cache?)
#  * Highlight featured programmes
#  * Configurable download location
#  * Auto-install / update get_iplayer

from __future__ import with_statement
import subprocess
import tempfile
import pickle
import os
import sys
import urllib
import cStringIO
import wx

class Series():
    pass

class Episode():
    pass


class IPlayer():
    if 'HOME' in os.environ:
        HOME_DIR = os.environ['HOME']
    elif 'USERPROFILE' in os.environ:
        HOME_DIR = os.environ['USERPROFILE']
    else:
        HOME_DIR = os.expanduser("~")

    PROFILE_DIR = os.path.join(HOME_DIR, ".get_iplayer")
    TV_CACHE_FILE = os.path.join(PROFILE_DIR, "tv.cache")
    OPTIONS_FILE = os.path.join(PROFILE_DIR, ".guiplayer")

    download_dir = "/home/pete/Movies"

    def __init__(self):
        self._refresh_cache()
        self._parse_cache()
        self.ignored_programmes = set()
        self.downloaded_episodes = set()
        try:
            file = open(self.OPTIONS_FILE, "r")
            self.ignored_programmes = pickle.load(file)
            self.downloaded_episodes = pickle.load(file)
        except:
            pass

    def __del__(self):
        file = open(self.OPTIONS_FILE, "w")
        pickle.dump(self.ignored_programmes, file)
        pickle.dump(self.downloaded_episodes, file)

    def download(self, episode):
        result = subprocess.check_call("get_iplayer --output %s --get %s" % 
                                       (self.download_dir, episode.Pid), 
                                       shell=True)
        self.mark_as_downloaded(episode)

    def mark_as_downloaded(self, episode):
        self.downloaded_episodes.add(episode.Pid)

    def _refresh_cache(self):
        result = subprocess.check_call("get_iplayer --quiet", shell=True)

    def _parse_cache(self):
        self.programmes = {}
        with open(self.TV_CACHE_FILE) as f:
            # Parse the headings
            first_line = f.readline().strip()
            if first_line[0] != "#":
                raise ValueError("Invalid cache file format")
            headings = first_line[1:].split("|")
            
            for line in f:
                # Create an episode object
                episode = Episode()
                split_line = line.split("|")
                for i,heading in enumerate(headings):
                    episode.__dict__[heading] = split_line[i]

                episode.Name = unicode(episode.Name, 'utf-8')

                # Create a new programme if necessary
                if episode.Name not in self.programmes:
                    self.programmes[episode.Name] = []
                    
                self.programmes[episode.Name].append(episode)

class IPlayerFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        IPlayerPanel(self)
        self.SetSize((800,600))    # Default size

class IPlayerPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs) 
        self.iplayer = IPlayer()
        self._make_widgets()

        self.programme_list.populate()

    def _make_widgets(self):
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.programme_list = ProgrammeList(self, self.iplayer)
        self.programme_list.list.Bind(wx.EVT_LIST_ITEM_SELECTED, 
                                      self._programme_change,
                                      self.programme_list.list)
        hbox.Add(self.programme_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        vbox = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, label="Episodes:")
        vbox.Add(label)

        self.episode_list = EpisodeList(self, self.iplayer, self._refresh_programme_list)
        self.episode_list.Bind(wx.EVT_LIST_ITEM_SELECTED, 
                               self._episode_change,
                               self.episode_list)
        vbox.Add(self.episode_list, proportion=1, flag=wx.EXPAND)

        self.episode_panel = EpisodePanel(self, self.iplayer, self._refresh_episode_list)
        vbox.Add(self.episode_panel, proportion=1, flag=wx.EXPAND)

        hbox.Add(vbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizerAndFit(hbox)

    def _programme_change(self, event):
        programme_name = event.GetText()
        if programme_name != "":
            self.episode_list.populate(self.iplayer.programmes[programme_name])
                
    def _episode_change(self, event):
        index = event.GetIndex()
        if index != wx.NOT_FOUND:
            episode = self.episode_list.programme[index]
            self.episode_panel.populate(episode)

    def _refresh_episode_list(self):
        self.episode_list.refresh()
 
    def _refresh_programme_list(self):
        self.programme_list.refresh()
               

class ProgrammeList(wx.Panel):
    DOWNLOADED_ITEM_COLOUR = wx.LIGHT_GREY

    def __init__(self, parent, iplayer):  
        wx.Panel.__init__(self, parent)
        self.iplayer = iplayer
        
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.list = wx.ListCtrl(self, style=wx.LC_REPORT |
                                            wx.LC_SINGLE_SEL |
                                            wx.LC_NO_HEADER)
        self.list.InsertColumn(0, "")
        self.list.Bind(wx.EVT_CHAR, self._on_key)
        vbox.Add(self.list, proportion=1, flag=wx.EXPAND)

        but_box = wx.BoxSizer(wx.HORIZONTAL)
        but = wx.Button(self, label="Delete")
        but.Bind(wx.EVT_BUTTON, self.delete_selected)
        but_box.Add(but)
        but = wx.Button(self, label="Show Deleted")
        but_box.Add(but, flag=wx.LEFT, border=5)
        vbox.Add(but_box, flag=wx.TOP, border=5)

        self.SetSizerAndFit(vbox)

    def _on_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            self.delete_selected()
        else:
            event.Skip()

    def populate(self, ignore=True):
        self.list.DeleteAllItems()
        self.list.SetColumnWidth(0, self.GetSize().width)

        for (name, programme) in sorted(self.iplayer.programmes.items()):
            if ignore and name in self.iplayer.ignored_programmes:
                continue

            item = self.list.InsertStringItem(sys.maxint, name)

            programme_pids = set([episode.Pid for episode in programme])
            if programme_pids.issubset(self.iplayer.downloaded_episodes):
                self.list.SetItemTextColour(item, self.DOWNLOADED_ITEM_COLOUR)

    def refresh(self):
        item = self.list.GetNextItem(-1, state=wx.LIST_STATE_SELECTED)
        self.populate()
        if item != -1:
            self.list.SetItemState(item, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def delete_selected(self, event=None):
        item = self.list.GetNextItem(-1, state=wx.LIST_STATE_SELECTED)
        if item == -1:
            return

        self.iplayer.ignored_programmes.add(self.list.GetItemText(item))
        self.list.DeleteItem(item)



class EpisodeList(wx.ListCtrl):
    DOWNLOADED_ITEM_COLOUR = wx.LIGHT_GREY

    def __init__(self, parent, iplayer, refresh_callback):
        self.iplayer = iplayer
        self.refresh_callback = refresh_callback
        self.programme = []
        wx.ListCtrl.__init__(self, parent, 
                             style=wx.LC_REPORT | 
                                   wx.LC_SINGLE_SEL |
                                   wx.LC_NO_HEADER)
        self.InsertColumn(0, "")

    def populate(self, programme):
        self.programme = programme

        self.DeleteAllItems()
        self.SetColumnWidth(0, self.GetSize().width)

        for episode in programme:
            item = self.InsertStringItem(sys.maxint, episode.Episode)

            if episode.Pid in self.iplayer.downloaded_episodes:
                self.SetItemTextColour(item, self.DOWNLOADED_ITEM_COLOUR)

        if len(programme) > 0:
            # Select the first item
            self.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def refresh(self):
        next_item = self.GetNextItem(-1, state=wx.LIST_STATE_SELECTED) + 1
        self.refresh_callback()
        self.populate(self.programme)
        if next_item != -1 and next_item < self.GetItemCount():
            self.SetItemState(next_item, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

class EpisodePanel(wx.Panel):
    def __init__(self, parent, iplayer, refresh_callback):
        self.iplayer = iplayer
        self.refresh_callback = refresh_callback
        self.episode = None
        wx.Panel.__init__(self, parent)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

#        self.thumbnail = wx.StaticBitmap(self)
#        hbox.Add(self.thumbnail)
        
        self.description = wx.TextCtrl(self, style=wx.TE_READONLY | 
                                                   wx.TE_MULTILINE)
        hbox.Add(self.description, proportion=2, flag=wx.EXPAND)

        vbox.Add(hbox, proportion=2, flag=wx.EXPAND | wx.TOP, border=20)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        but = wx.Button(self, label="Download")
        but.Bind(wx.EVT_BUTTON, self.download)
        hbox.Add(but, flag=wx.ALL, border=5)

        but = wx.Button(self, label="Mark as Downloaded")
        but.Bind(wx.EVT_BUTTON, self.mark_as_downloaded)
        hbox.Add(but, flag=wx.ALL, border=5)

        vbox.Add(hbox)
        vbox.AddStretchSpacer(1)

        self.SetSizerAndFit(vbox)

    def populate(self, episode):
        self.episode = episode
        
        self.description.ChangeValue(episode.Desc)

# Works, but is synchonous -> slow!        
#        data = urllib.urlopen(episode.Thumbnail).read()
#        stream = cStringIO.StringIO(data)
#        bmp = wx.BitmapFromImage(wx.ImageFromStream(stream))
#        self.thumbnail.SetBitmap(bmp)

    def download(self, event):
        self.iplayer.download(self.episode)
        pass

    def mark_as_downloaded(self, event):
        self.iplayer.mark_as_downloaded(self.episode)
        self.refresh_callback()


def run():
    app = wx.App(redirect=False)
    frame = IPlayerFrame(parent=None, title="BBC iPlayer Downloader")
    frame.Show()
    app.MainLoop()

if __name__ == "__main__": 
    run()
