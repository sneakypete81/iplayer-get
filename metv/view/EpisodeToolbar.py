import wx
import images

class EpisodeToolbar(wx.ToolBar):
    ID_DOWNLOAD = 101
    ID_IGNORE = 102

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT|wx.TB_TEXT
        wx.ToolBar.__init__(self, *args, **kwds)
        self.AddLabelTool(self.ID_DOWNLOAD, 
                          label="Download", 
                          bitmap=images.getIPlayerBitmap(), 
                          shortHelp="Download the selected episode")
        self.AddLabelTool(self.ID_IGNORE, 
                          label="Ignore", 
                          bitmap=images.getIPlayerBitmap(), 
                          kind=wx.ITEM_CHECK, 
                          shortHelp="Mark the selected episode as \"Ignored\"")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetToolBitmapSize((48, 48))
        self.Realize()

    def __do_layout(self):
        pass

    def update(self, episode):
        if episode is None:
            ignored = False
        else:
            ignored = episode.ignored
        self.ToggleTool(self.ID_IGNORE, ignored)