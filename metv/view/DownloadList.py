#!/usr/bin/env python
import wx

class DownloadList(wx.ListCtrl):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        self.downloader = None

        self.InsertColumn(0, "Episode")
        self.InsertColumn(1, "Status")

    def set_downloader(self, downloader):
        self.downloader = downloader
        self.update()

    def update(self):
        if self.downloader is not None:
            count = len(self.downloader.episodes)
            self.SetItemCount(count)
            self.RefreshItems(0, count-1)

    def OnGetItemText(self, item, col):
        if col == 0:
            return self.downloader.episodes[item].name
        elif col == 1:
            return self.downloader.episodes[item].download_message
        else:
            return ""
