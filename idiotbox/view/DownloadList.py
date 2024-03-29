#!/usr/bin/env python
import wx
import wx.lib.mixins.listctrl as listmix

class DownloadList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.downloader = None

        self.InsertColumn(0, "Episode")
        self.InsertColumn(1, "Status")
        self.SetColumnWidth(0, 200)

    def set_downloader(self, downloader):
        self.downloader = downloader
        self.update()

    def update(self):
        if self.downloader is not None:
            count = len(self.downloader.episodes)
            self.SetItemCount(count)
            self.RefreshItems(0, count-1)

    def get_selected_episode(self):
        item = self.GetNextItem(wx.NOT_FOUND,
                                wx.LIST_NEXT_ALL,
                                wx.LIST_STATE_SELECTED);
        if (item == wx.NOT_FOUND):
            return None
        else:
            return self.downloader.episodes[item]


    def OnGetItemText(self, item, col):
        if col == 0:
            return (self.downloader.episodes[item].name + " - " +
                    self.downloader.episodes[item].episode)
        elif col == 1:
            return self.downloader.episodes[item].download_message
        else:
            return ""
