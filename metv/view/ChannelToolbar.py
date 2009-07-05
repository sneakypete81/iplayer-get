import wx
import images

class ChannelToolbar(wx.ToolBar):
    ID_SUBSCRIBE = 101
    ID_UNSUBSCRIBE = 102

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT|wx.TB_TEXT
        wx.ToolBar.__init__(self, *args, **kwds)
        self.AddLabelTool(self.ID_SUBSCRIBE, 
                          label="Subscribe", 
                          bitmap=images.getIPlayerBitmap(),
                          shortHelp="Add a new programme to the list")
        self.AddLabelTool(self.ID_UNSUBSCRIBE, 
                          label="Unsubscribe", 
                          bitmap=images.getIPlayerBitmap(),
                          shortHelp="Remove selected programme from the list")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetToolBitmapSize((48, 48))
        self.Realize()

    def __do_layout(self):
        pass



