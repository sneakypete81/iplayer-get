#!/usr/bin/env python

# Todo:
#  * Allow deleted programmes to be reshown / undeleted
#  * Thumbnails (cache?)
#  * Highlight featured programmes
#  * Configurable download location
#  * Auto-install / update get_iplayer

import async_subprocess as subprocess
import time
import tempfile
import pickle
import copy
import os
import sys
import urllib
import cStringIO
import wx
import wx.lib.mixins.listctrl as listmix

import iplayer_icon

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
    ITV_CACHE_FILE = os.path.join(PROFILE_DIR, "itv.cache")
    CH4_CACHE_FILE = os.path.join(PROFILE_DIR, "ch4.cache")
    FIVE_CACHE_FILE = os.path.join(PROFILE_DIR, "five.cache")
    OPTIONS_FILE = os.path.join(PROFILE_DIR, ".guiplayer")

    download_dir = "/home/pete/Movies"

    def __init__(self, log, progress):
        self.log = log
        self.programmes = {}

        progress.Pulse("Downloading BBC Programme List...")
        self._refresh_cache("tv", progress)
        self._parse_cache(self.TV_CACHE_FILE)
        progress.Pulse("Downloading ITV Programme List...")
        self._refresh_cache("itv", progress)
        self._parse_cache(self.ITV_CACHE_FILE)
        progress.Pulse("Downloading Channel 4 Programme List...")
        self._refresh_cache("ch4", progress)
        self._parse_cache(self.CH4_CACHE_FILE)
        progress.Pulse("Downloading Five Programme List...")
        self._refresh_cache("five", progress)
        self._parse_cache(self.FIVE_CACHE_FILE)

        self.ignored_programmes = set()
        self.downloaded_episodes = set()
        self.ignored_episodes = set()
        self.log.write("Reading options file...")
        try:
            file = open(self.OPTIONS_FILE, "r")
            self.ignored_programmes = pickle.load(file)
            self.downloaded_episodes = pickle.load(file)
            self.ignored_episodes = pickle.load(file)
        except Exception, inst:
            self.log.write("Error reading options file: %s" % str(inst))
            pass

    def __del__(self):
        if self.ignored_programmes != None and self.downloaded_episodes != None:
            file = open(self.OPTIONS_FILE, "w")
            pickle.dump(self.ignored_programmes, file)
            pickle.dump(self.downloaded_episodes, file)
            pickle.dump(self.ignored_episodes, file)

    def mark_as_downloaded(self, episode):
        self.log.write("Marking episode %s as downloaded..." % episode.pid)
        self.downloaded_episodes.add(episode.pid)

    def mark_as_ignored(self, episode):
        self.log.write("Marking episode %s as ignored..." % episode.pid)
        self.ignored_episodes.add(episode.pid)

    def _refresh_cache(self, type, progress):
        self.log.write("Refreshing %s cache..." % type)
        proc = subprocess.Popen("get_iplayer " +
                                "--refresh " + # Force update of cache
                                "--type=%s " % type +
                                "--quiet", 
                                shell=True,
                                stdout=subprocess.PIPE)
        while proc.poll() == None:
            progress.Pulse()
            time.sleep(0.04)

    def _parse_cache(self, cache_file):
        self.log.write("Parsing cache %s..." % cache_file)
        f = open(cache_file)
        # Parse the headings
        first_line = f.readline().strip()
        if first_line[0] != "#":
            self.log.write("Invalid cache file format.")
            self.log.write("First line was: '%s'" % first_line)
            raise ValueError("Invalid cache file format.")

        headings = first_line[1:].split("|")       
        self.log.write("Cache headings: %s" % str(headings))

        lines = f.readlines()
        self.log.write("Parsing %d lines from cache..." % len(lines))

        for line in lines:
            # Create an episode object
            episode = Episode()
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

            # Create a new programme if necessary
            if episode.name not in self.programmes:
                self.programmes[episode.name] = []
                
            self.programmes[episode.name].append(episode)

        self.log.write("Cache parsing complete.")

class IPlayerFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = IPlayerPanel(self)
        self.SetSize((800,600))    # Default size

        self.SetIcon(iplayer_icon.getIplayerIcon())

        self.Bind(wx.EVT_CLOSE, self._on_close)

    def _on_close(self, event):
        if event.CanVeto() and self.panel.download_tab.list.queue_size > 0:
            try:
                dlg = wx.MessageDialog(self, "There are downloads in progress.\n" +
                                       "Are you sure you want to exit?", 
                                       "BBC iPlayer Downloader",
                                       wx.YES_NO|wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_NO:
                    event.Veto()
                    return
            finally:
                dlg.Destroy

        self.Destroy()

class IPlayerPanel(wx.Panel):
    TAB_PROGRAMME = 0
    TAB_DOWNLOAD = 1
    TAB_LOG = 2

    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs) 

        self.nb = wx.Notebook(self, style=wx.NB_TOP) 

        self.log = LogTab(self.nb)

        progress = wx.ProgressDialog(parent=self, 
                                     message="Downloading BBC Programme List...",
                                     title="BBC iPlayer Downloader")
        progress.CentreOnScreen()
        progress.SetIcon(iplayer_icon.getIplayerIcon())

        iplayer = IPlayer(self.log, progress)
        progress.Destroy()

        self.programme_tab = ProgrammeTab(self.nb, 
                                iplayer, 
                                download_callback=self._download_episode,
                                log=self.log)
        self.download_tab = DownloadTab(self.nb, 
                                iplayer, 
                                refresh_callback=self._download_complete,
                                log=self.log)

        self.nb.InsertPage(self.TAB_PROGRAMME, self.programme_tab, "Programmes")
        self.nb.InsertPage(self.TAB_DOWNLOAD, self.download_tab, "Downloads")
        self.nb.InsertPage(self.TAB_LOG, self.log, "Log")

        topbox = wx.BoxSizer(wx.VERTICAL)
        topbox.Add(self.nb, proportion=1, flag=wx.EXPAND)
        self.SetSizerAndFit(topbox)

    def _download_episode(self, episode):
        self.download_tab.add(episode)
        self._update_download_count()

    def _download_complete(self):
        self.programme_tab.refresh()
        self._update_download_count()

    def _update_download_count(self):
        """ Update the count in the download tab title """
        count = self.download_tab.list.queue_size
        if count == 0:
            text = "Downloads"
        else:
            text = "Downloads (%d)" % count

        self.nb.SetPageText(self.TAB_DOWNLOAD, text)
        
class ProgrammeTab(wx.Panel):
    def __init__(self, parent, iplayer, download_callback, log):
        wx.Panel.__init__(self, parent) 
        self.iplayer = iplayer
        self.log = log
        self.download_callback = download_callback

        topbox = wx.BoxSizer(wx.HORIZONTAL)

        self.programme_list = ProgrammeList(self, self.iplayer, log=self.log)
        self.programme_list.list.Bind(wx.EVT_LIST_ITEM_SELECTED, 
                                      self._programme_change,
                                      self.programme_list.list)
        topbox.Add(self.programme_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.episode_title = wx.StaticText(self, label="")
        title_font = self.episode_title.GetFont()
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.episode_title.SetFont(title_font)
        vbox.Add(self.episode_title)

        self.episode_list = EpisodeList(self, self.iplayer)
        vbox.Add(self.episode_list, proportion=1, flag=wx.EXPAND)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        but = wx.Button(self, label="Download")
        but.Bind(wx.EVT_BUTTON, self.download)
        hbox.Add(but)

        but = wx.Button(self, label="Ignore")
        but.Bind(wx.EVT_BUTTON, self.mark_as_ignored)
        hbox.Add(but, flag=wx.LEFT, border=5)

        vbox.Add(hbox, flag=wx.TOP, border=5)

        topbox.Add(vbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizerAndFit(topbox)
        self.populate()

    def populate(self):
        self.programme_list.populate()

    def _programme_change(self, event):
        programme_name = event.GetText()
        if programme_name != "":
            self.episode_title.SetLabel(programme_name)
            programme = self.iplayer.programmes[programme_name]

            self.episode_list.populate(programme)
                
    def refresh(self):
        self._refresh_episode_list()
        self._refresh_programme_list()

    def download(self, event):
        episode = self.episode_list.get_selected_episode()
        if episode is not None:
            self.download_callback(episode)

    def mark_as_downloaded(self, event):
        episode = self.episode_list.get_selected_episode()
        if episode is not None:
            self.iplayer.mark_as_downloaded(episode)
            self.refresh()

    def mark_as_ignored(self, event):
        episode = self.episode_list.get_selected_episode()
        if episode is not None:
            self.iplayer.mark_as_ignored(episode)
            self.refresh()

    def _refresh_programme_list(self):
        self.programme_list.refresh()

    def _refresh_episode_list(self):
        self.episode_list.Refresh()
 
class ProgrammeList(wx.Panel):
    DOWNLOADED_OR_IGNORED_ITEM_COLOUR = wx.LIGHT_GREY

    def __init__(self, parent, iplayer, log):  
        self.iplayer = iplayer
        self.log = log

        wx.Panel.__init__(self, parent)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.list = wx.ListCtrl(self, style=wx.LC_REPORT |
                                            wx.LC_SINGLE_SEL |
                                            wx.LC_NO_HEADER |
                                            wx.BORDER_SUNKEN)
        self.list.InsertColumn(0, "")
        self.list.Bind(wx.EVT_CHAR, self._on_key)
        vbox.Add(self.list, proportion=1, flag=wx.EXPAND)

        but_box = wx.BoxSizer(wx.HORIZONTAL)
        but = wx.Button(self, label="Delete")
        but.Bind(wx.EVT_BUTTON, self.delete_selected)
        but_box.Add(but)
        but = wx.Button(self, label="Show Deleted...")
        but.Bind(wx.EVT_BUTTON, self.show_deleted)
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
        bbc_programmes = [p for p in self.iplayer.programmes.items() 
                          if p[1][0].type == "tv"]
        other_programmes = [p for p in self.iplayer.programmes.items() 
                            if p[1][0].type != "tv"]

        for (name, programme) in sorted(bbc_programmes):
            self.add_programme(name, programme, ignore)
        for (name, programme) in sorted(other_programmes):
            self.add_programme(name, programme, ignore)


        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def add_programme(self, name, programme, ignore):
        # Don't compare episode-specific title text
        name_root = self.name_root(name)
        if ignore and name_root in self.iplayer.ignored_programmes:
            return

        item = self.list.InsertStringItem(sys.maxint, name)

        programme_pids = set([episode.pid for episode in programme])
        ignored_or_downloaded = self.iplayer.downloaded_episodes.union \
                                (self.iplayer.ignored_episodes)
        if programme_pids.issubset(ignored_or_downloaded):
            self.list.SetItemTextColour(item, 
                                        self.DOWNLOADED_OR_IGNORED_ITEM_COLOUR)

    def refresh(self):
        item = self.list.GetNextItem(-1, state=wx.LIST_STATE_SELECTED)
        self.populate()
        if item != -1:
            self.list.SetItemState(item, 
                                   wx.LIST_STATE_SELECTED, 
                                   wx.LIST_STATE_SELECTED)

    def delete_selected(self, event=None):
        item = self.list.GetNextItem(-1, state=wx.LIST_STATE_SELECTED)
        if item == -1:
            return

        name_root = self.name_root(self.list.GetItemText(item))
        self.log.write("Deleting programme %s..." % name_root)
        self.iplayer.ignored_programmes.add(name_root)
        self.list.DeleteItem(item)

        # Select the next item automatically
        if item >= self.list.GetItemCount():
            item -= 1
        if item >= 0:
            self.list.SetItemState(item, 
                                   wx.LIST_STATE_SELECTED, 
                                   wx.LIST_STATE_SELECTED)

    def name_root(self, name):
        return name.split(": Series")[0]

    def show_deleted(self, event=None):
        current_deleted_names = [name for name in self.iplayer.programmes.keys()
                                 if self.name_root(name) in self.iplayer.ignored_programmes]
        current_deleted_names.sort()
        dlg = wx.MultiChoiceDialog(self, 
                                   "Select programmes to restore:",
                                   "Deleted Programmes",
                                   current_deleted_names)
        dlg.SetSize((-1, self.GetSize().height))
        if dlg.ShowModal() == wx.ID_OK:
            for item in dlg.GetSelections():
                name_root = self.name_root(current_deleted_names[item])
                self.log.write("Restoring programme %s..." % name_root)
                try:
                    self.iplayer.ignored_programmes.remove(name_root)
                except KeyError:
                    self.log.write("Programme not found in deleted list.")
            self.refresh()


class EpisodeList(wx.HtmlListBox):
    def __init__(self, parent, iplayer):
        self.iplayer = iplayer
        self.programme = []
        wx.HtmlListBox.__init__(self, parent, style=wx.BORDER_SUNKEN)

    def populate(self, programme): 
        self.programme = programme
        self.SetItemCount(len(programme))
        self.Refresh()

        # Automatically select the first un-downloaded/ignored episode
        for (index, episode) in enumerate(programme):
            if episode.pid not in self.iplayer.downloaded_episodes and \
               episode.pid not in self.iplayer.ignored_episodes:
                self.SetSelection(index)
                return
        self.SetSelection(-1)

    def OnGetItem(self, index):
        episode = self.programme[index]

        if episode.pid in self.iplayer.downloaded_episodes:
            html = ("<font color=grey>%s</font><br>" % episode.episode +
                    "<table><td>&nbsp;</td><td>" + # Indent
                    "<font color=grey size=-1>%s</font>" % episode.desc +
                    "</td></table>")
        elif episode.pid in self.iplayer.ignored_episodes:
            html = ("<font color=red>%s</font><br>" % episode.episode +
                    "<table><td>&nbsp;</td><td>" + # Indent
                    "<font color=red size=-1>%s</font>" % episode.desc +
                    "</td></table>")
        else:
            html = ("<strong>%s</strong><br>" % episode.episode +
                    "<table><td>&nbsp;</td><td>" + # Indent
                    "<font size=-1>%s</font>" % episode.desc +
                    "</td></table>")
        
        return html

    def get_selected_episode(self):
        index = self.GetSelection() 
        if index == wx.NOT_FOUND:
            return None
        else:
            return self.programme[index]


class DownloadTab(wx.Panel):
    def __init__(self, parent, iplayer, log, refresh_callback):
        self.iplayer = iplayer
        self.log = log
        wx.Panel.__init__(self, parent)

        topbox = wx.BoxSizer(wx.VERTICAL)
        self.list = DownloadList(self, self.iplayer, log=self.log,
                                 refresh_callback=refresh_callback)
        topbox.Add(self.list, 
                   proportion=1, 
                   border=5,
                   flag=wx.EXPAND | wx.ALL)

        self.SetSizerAndFit(topbox)

    def add(self, episode):
        self.list.add(episode)

class DownloadList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    PROCESS_READ_INTERVAL = 200 # suck on the pipe every 200ms
    
    def __init__(self, parent, iplayer, log, refresh_callback):
        self.iplayer = iplayer
        self.log = log
        self.refresh_callback = refresh_callback
        self.current_item = None
        self.episodes = {}
        self.queue_size = 0
        wx.ListCtrl.__init__(self, parent, 
                             style=wx.LC_REPORT | 
                                   wx.LC_SINGLE_SEL |
                                   wx.BORDER_SUNKEN)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.InsertColumn(0, "Episode")
        self.COL_EPISODE = 0
        self.InsertColumn(1, "Status")
        self.COL_STATUS = 1
        self.InsertColumn(2, "Size")
        self.COL_SIZE = 2
        self.InsertColumn(3, "Progress")
        self.COL_PROGRESS = 3
        self.InsertColumn(4, "Speed")
        self.COL_SPEED = 4
        self.InsertColumn(5, "Remaining Time")
        self.COL_REMAINING_TIME = 5
        self.size_columns()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer)
        self.process = None

    def __del__(self):
        if self.process is not None:
            self.process.kill()
            self.timer.Stop()

    def size_columns(self):
        self.InsertStringItem(self.COL_EPISODE, "Hello")
        self.SetStringItem(0, self.COL_STATUS, "Downloading")
        self.SetColumnWidth(self.COL_STATUS, wx.LIST_AUTOSIZE)
        self.SetStringItem(0, self.COL_SIZE, "888.88MB / 888.88MB")
        self.SetColumnWidth(self.COL_SIZE, wx.LIST_AUTOSIZE)
        self.SetStringItem(0, self.COL_PROGRESS, "100%")
        self.SetColumnWidth(self.COL_PROGRESS, wx.LIST_AUTOSIZE_USEHEADER)
        self.SetStringItem(0, self.COL_SPEED, "88888kbps")
        self.SetColumnWidth(self.COL_SPEED, wx.LIST_AUTOSIZE)
        self.SetStringItem(0, self.COL_REMAINING_TIME, "88:88:88")
        self.SetColumnWidth(self.COL_REMAINING_TIME, wx.LIST_AUTOSIZE_USEHEADER)
        self.setResizeColumn(self.COL_EPISODE+1) # +1 due to wxPython bug
        self.DeleteItem(0)

    def add(self, episode):
        self.log.write("Adding episode %s to the download queue." % episode.pid)
        label = "%s: %s" % (episode.name, episode.episode)
        item = self.InsertStringItem(sys.maxint, label)

        # Take a copy, so we can handle multiple instances of the same episode
        self.episodes[item] = copy.copy(episode)
        episode = self.episodes[item]
        
        episode.queued = True
        episode.error = False
        episode.error_message = ""
        self.SetStringItem(item, self.COL_STATUS, "Queued")
        self.episodes[item] = episode
        self.queue_size += 1

        if self.current_item is None:
            self.download_next()

    def download_next(self):
        queued_episodes = [item for (item, episode) in self.episodes.items()
                            if episode.queued]
        if queued_episodes == []:
            self.log.write("No more episodes in download queue.")
            return

        self.download(queued_episodes[0])

    def download(self, item):
        episode = self.episodes[item]
        self.SetStringItem(item, self.COL_STATUS, "Downloading")
        self.current_item = item
        self.log.write("Downloading episode %s..." % episode.pid)
        cmd = ("get_iplayer " +
               "--force-download " +
               "--vmode=iphone " +
               "--vmode=flashvhigh,flashhigh,iphone,flashnormal " +
               "--file-prefix \"<name> <availabledate> <episode> <pid>\" " +
               "--output %s " % self.iplayer.download_dir +
               "--pid %s" % episode.pid)

        try:
            self.process = subprocess.Popen(cmd, shell=True, 
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
        except OSError, inst:
            episode.error = True
            episode.error_message = ("Could not execute get_iplayer " +
                                     "(%s)" % str(inst))
            self.log.error(error_message)
            self._on_process_ended()
            return

        self.data = ""
        self.timer.Start(self.PROCESS_READ_INTERVAL)
        self.log.write("Started get_iplayer process.")
        
    def read(self):
        data = self.process.recv()
        if data is not None:
            data = self.data + data

        # Split at \n's and \r's
            lines = data.split("\n")
            items = []
            for line in lines:
                items += line.split("\r")

            while len(items) > 1:
                self._process_line(items.pop(0).strip())
            self.data = items[0]

        exitcode = self.process.poll()
        if exitcode is not None:
            if data is None:
                if exitcode != 0:
                    episode.error = True
                    episode.error_message = ("Error executing get_iplayer " +
                                             "(Error code %d)" % exitcode)
                    self.log.error(error_message)

                self._on_process_ended()
            else: # Recurse until there's no data left in the pipe
                self.read()

    def _process_line(self, line):
        self.log.write("get-iplayer : %s" % line)
        if line.startswith("ERROR:"):
            error_message = line[6:].strip()
            self.log.error(error_message)
            self.episodes[self.current_item].error = True
            self.episodes[self.current_item].error_message += error_message
        if not self._process_rtmpdump_line(line):
            self._process_iphone_line(line)

            
    def _process_iphone_line(self, line):
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
            
            self.SetStringItem(self.current_item, self.COL_SIZE, 
                               "%s / %s" % (downloaded.strip(), size.strip()))
            self.SetStringItem(self.current_item, self.COL_PROGRESS, 
                               "%s%%" % percent.strip())
            self.SetStringItem(self.current_item, self.COL_SPEED, 
                               rate.strip())
            self.SetStringItem(self.current_item, self.COL_REMAINING_TIME, 
                               remaining_time.strip())
            return True
        except ValueError, msg:
            # Couldn't understand the line - ignore
            return False
            
    def _process_rtmpdump_line(self, line):
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
            
            self.SetStringItem(self.current_item, self.COL_SIZE, 
                               "%s" % downloaded.strip())
            self.SetStringItem(self.current_item, self.COL_PROGRESS, 
                               "%s%%" % percent.strip())
            return True

        except ValueError, msg:
            # Couldn't understand the line - ignore
            return False
            
    def _on_timer(self, event):
        self.read()

    def _on_process_ended(self, event=None):
        episode = self.episodes[self.current_item]
        self.log.write("get-iplayer process ended")
        self.process = None
        self.timer.Stop()

        self.SetStringItem(self.current_item, self.COL_STATUS, "Downloaded")
        self.SetStringItem(self.current_item, self.COL_SIZE, "")
        self.SetStringItem(self.current_item, self.COL_PROGRESS, "")
        self.SetStringItem(self.current_item, self.COL_SPEED, "")
        self.SetStringItem(self.current_item, self.COL_REMAINING_TIME, "")

        if episode.error:
            self.SetStringItem(self.current_item, self.COL_STATUS, "Error: %s" %
                               episode.error_message)
        else:
            self.iplayer.mark_as_downloaded(episode)
            
        self.queue_size -= 1
        self.refresh_callback()

        episode.queued = False
        self.current_item = None
        self.download_next()


class LogTab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        topbox = wx.BoxSizer(wx.VERTICAL)
        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | 
                                            wx.TE_READONLY |
                                            wx.BORDER_SUNKEN)
        bg = self.text.GetBackgroundColour()
        self.text.Enable(False)
        self.text.SetBackgroundColour(bg)
        topbox.Add(self.text, 
                   proportion=1, 
                   border=5,
                   flag=wx.EXPAND | wx.ALL)

        self.SetSizerAndFit(topbox)

    def write(self, text):
        self.text.WriteText("%s\n" % text)


    def error(self, text):
        self.text.WriteText("***********\n")
        self.text.WriteText("*** ERROR : %s\n" % text)
        self.text.WriteText("***********\n")

def run():
    app = wx.App(redirect=False)
    frame = IPlayerFrame(parent=None, title="BBC iPlayer Downloader")
    frame.Show()
    app.MainLoop()

if __name__ == "__main__": 
    run()
