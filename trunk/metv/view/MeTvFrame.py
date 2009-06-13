# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Wed May 13 21:21:56 2009

import wx

# begin wxGlade: dependencies
# end wxGlade
from ChannelToolbar import ChannelToolbar
from EpisodeToolbar import EpisodeToolbar
from ChannelTree import ChannelTree
from EpisodeList import EpisodeList
from DownloadList import DownloadList

# begin wxGlade: extracode

# end wxGlade

class MeTvFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.app = wx.App(0)
        kwds['parent'] = None

        # begin wxGlade: MeTvFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.notebook = wx.Notebook(self, -1, style=0)
        self.notebook_downloads = wx.Panel(self.notebook, -1)
        self.notebook_programmes = wx.Panel(self.notebook, -1)
        self.episode_panel = wx.Panel(self.notebook_programmes, -1)
        self.channel_panel = wx.Panel(self.notebook_programmes, -1)
        self.channel_toolbar = ChannelToolbar(self.channel_panel, -1)
        self.channel_tree = ChannelTree(self.channel_panel, -1, style=wx.TR_HAS_BUTTONS|wx.TR_NO_LINES|wx.TR_LINES_AT_ROOT|wx.TR_HIDE_ROOT|wx.TR_DEFAULT_STYLE|wx.STATIC_BORDER)
        self.static_line_1 = wx.StaticLine(self.notebook_programmes, -1, style=wx.LI_VERTICAL)
        self.episode_toolbar = EpisodeToolbar(self.episode_panel, -1)
        self.episode_list = EpisodeList(self.episode_panel, -1, choices=[])
        self.download_list = DownloadList(self.notebook_downloads, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.SUNKEN_BORDER)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MeTvFrame.__set_properties
        self.SetTitle("meTV")
        self.SetSize((600, 500))
        self.episode_list.SetWindowStyle(wx.STATIC_BORDER)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MeTvFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_1_copy = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.channel_toolbar, 0, wx.EXPAND, 2)
        sizer_2.Add(self.channel_tree, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        self.channel_panel.SetSizer(sizer_2)
        sizer_1_copy.Add(self.channel_panel, 3, wx.EXPAND, 0)
        sizer_1_copy.Add(self.static_line_1, 0, wx.EXPAND, 0)
        sizer_4.Add(self.episode_toolbar, 0, wx.EXPAND, 2)
        sizer_4.Add(self.episode_list, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        self.episode_panel.SetSizer(sizer_4)
        sizer_1_copy.Add(self.episode_panel, 4, wx.EXPAND, 0)
        self.notebook_programmes.SetSizer(sizer_1_copy)
        sizer_3.Add(self.download_list, 1, wx.EXPAND, 0)
        self.notebook_downloads.SetSizer(sizer_3)
        self.notebook.AddPage(self.notebook_programmes, "Programmes")
        self.notebook.AddPage(self.notebook_downloads, "Downloads")
        sizer_1.Add(self.notebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def start(self):
        self.Show()
        self.app.MainLoop()

# Channel Panel
###############

#     def delete_all_channels(self):
#         self.channel_panel.clear()

#     def add_channel(self, channel):
#         self.channel_panel.add(channel)
            
#     def update_channel(self, channel):
#         self.channel_panel.update(channel)

#     def refresh_selected_programme(self):
#         self.channel_panel.refresh_selected_programme()

#     def get_selected_programme(self):
#         return self.channel_panel.get_selected_programme()

#     def delete_programme(self, programme):
#         self.channel_panel.delete_programme(programme)

# # Episode Panel
# ###############

#     def update_episodes(self, programme):
#         self.episode_panel.update(programme)

#     def get_selected_episode(self):
#         return self.episode_panel.get_selected_episode()

#     def refresh_selected_episode(self):
#         self.episode_panel.refresh_selected_episode()

#     def select_next_episode(self):
#         self.episode_panel.select_next_episode()

#     def update_episode_toolbar(self, episode):
#         self.episode_panel.update_episode_toolbar(episode)

# # Download List
# ###############

#     def update_downloads(self, downloader):
#         self.download_list.update(downloader)

# # Download Log
# ##############

#     def update_log(self, episode):
#         self.download_log.update(episode)



# end of class MeTvFrame


