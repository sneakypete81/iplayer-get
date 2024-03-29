# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Sun Jun 28 17:43:18 2009

import wx

# begin wxGlade: dependencies
from SubscriptionsPane import SubscriptionsPane
# end wxGlade

# begin wxGlade: extracode

# end wxGlade

class SubscriptionsDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: SubscriptionsDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.notebook = wx.Notebook(self, -1, style=0)
        self.notebook_1_pane_1 = SubscriptionsPane(self.notebook, -1)
        self.button_1 = wx.Button(self, wx.ID_CLOSE, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self._on_close, self.button_1)
        # end wxGlade

        # This pane is just for design time - delete it.
        self.notebook.RemovePage(0)
        self.notebook_1_pane_1.Destroy()

        self.panes = {}

    def __set_properties(self):
        # begin wxGlade: SubscriptionsDialog.__set_properties
        self.SetTitle("Manage Subscriptions")
        self.SetSize((600, 400))
        self.button_1.SetDefault()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: SubscriptionsDialog.__do_layout
        sizer_6 = wx.BoxSizer(wx.VERTICAL)
        self.notebook.AddPage(self.notebook_1_pane_1, "tab1")
        sizer_6.Add(self.notebook, 1, wx.EXPAND, 0)
        sizer_6.Add(self.button_1, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        self.SetSizer(sizer_6)
        self.Layout()
        # end wxGlade

    def _on_close(self, event): # wxGlade: SubscriptionsDialog.<event_handler>
        self.Close()

    def ShowModal(self, *args, **kwds):
        channels = kwds.pop("channels")

        for channel in channels:
            pane = SubscriptionsPane(self.notebook, channel=channel) 
            self.panes[channel.title] = pane
            self.notebook.AddPage(page=pane, caption=channel.title)

        wx.Dialog.ShowModal(self, *args, **kwds)
        
        # Remove and destroy all tabs
        for page in range(self.notebook.GetPageCount()):
            self.notebook.RemovePage(0)
        for pane in self.panes.values():
            pane.Destroy()
        self.panes = {}


# end of class SubscriptionsDialog


