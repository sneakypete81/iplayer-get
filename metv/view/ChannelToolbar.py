# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Wed May 13 20:53:38 2009

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode

# end wxGlade

class ChannelToolbar(wx.ToolBar):
    ID_SUBSCRIBE = 101
    ID_UNSUBSCRIBE = 102

    def __init__(self, *args, **kwds):
        # begin wxGlade: ChannelToolbar.__init__
        kwds["style"] = wx.TB_FLAT|wx.TB_TEXT
        wx.ToolBar.__init__(self, *args, **kwds)
        self.AddLabelTool(self.ID_SUBSCRIBE, "Subscribe", wx.Bitmap("C:\\linuxshare\\projects\\iplayer-get\\metv\\view\\iplayer-temp.png", wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, "Add a new programme to the list", "")
        self.AddLabelTool(self.ID_UNSUBSCRIBE, "Unsubscribe", wx.Bitmap("C:\\linuxshare\\projects\\iplayer-get\\metv\\view\\iplayer-temp.png", wx.BITMAP_TYPE_ANY), wx.NullBitmap, wx.ITEM_NORMAL, "Remove selected programme from the list", "")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ChannelToolbar.__set_properties
        self.SetToolBitmapSize((48, 48))
        self.Realize()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ChannelToolbar.__do_layout
        pass
        # end wxGlade

# end of class ChannelToolbar


