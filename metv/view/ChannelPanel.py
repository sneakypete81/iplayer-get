# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Wed May 13 20:53:38 2009

import wx
import operator

from ChannelToolbar import ChannelToolbar
# begin wxGlade: dependencies
# end wxGlade

NORMAL_TEXT_COLOUR = "BLACK"
REFRESH_TEXT_COLOUR = "DIM GREY"
ERROR_TEXT_COLOUR = "RED"
DOWNLOADED_TEXT_COLOUR = "DIM GREY"

class ChannelPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ChannelPanel.__init__
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.channel_toolbar = ChannelToolbar(self, -1)
        self.tree = wx.TreeCtrl(self, -1, style=wx.TR_HAS_BUTTONS|wx.TR_NO_LINES|wx.TR_LINES_AT_ROOT|wx.TR_HIDE_ROOT|wx.TR_DEFAULT_STYLE|wx.STATIC_BORDER)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ChannelPanel.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ChannelPanel.__do_layout
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.channel_toolbar, 0, wx.EXPAND, 2)
        sizer_2.Add(self.tree, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        # end wxGlade

    def clear(self):
        """ Remove all data from the tree """
        self.tree.DeleteAllItems()
        self._root = self.tree.AddRoot(text="")

    def add(self, channel):
        """ Add a new channel to the tree """
        item = self.tree.AppendItem(parent=self._root,
                                    text=channel.title,
                                    data=wx.TreeItemData(channel))
        channel.view_item = item
        self.update(channel)
        self.tree.Expand(item)

    def update(self, channel):
        """ Update the tree data for the specified channel """
        channel_item = channel.view_item
        self.tree.DeleteChildren(channel_item)
        if channel.is_refreshing:
            refresh_text = self.tree.AppendItem(parent=channel_item,
                                                text="Refreshing...")
            self.tree.SetItemTextColour(refresh_text, 
                                        wx.NamedColour(REFRESH_TEXT_COLOUR))
        elif channel.error_message is not None:
            refresh_text = self.tree.AppendItem(parent=channel_item,
                                                text="ERROR: %s" % channel.error_message)
            self.tree.SetItemTextColour(refresh_text, 
                                        wx.NamedColour(ERROR_TEXT_COLOUR))
        else:
            programmes = channel.programmes.values()
            programmes.sort(key=operator.attrgetter('name'))
            for programme in programmes:
                item = self.tree.AppendItem(parent=channel_item,
                                            text=programme.name,
                                            data=wx.TreeItemData(programme))
                programme.view_item = item
                self.update_programme_text_colour(programme)

    def refresh_selected_programme(self):
        self.update_programme_text_colour(self.get_selected_programme())

    def update_programme_text_colour(self, programme):
        """ Update the display colour of the specified programme """
        if programme is not None:
            for episode in programme.episodes:
                if not episode.downloaded and not episode.ignored:
                    self.tree.SetItemTextColour(programme.view_item,
                                                wx.NamedColour(NORMAL_TEXT_COLOUR))
                    return
            # Programme contains only downloaded or ignored episodes
            self.tree.SetItemTextColour(programme.view_item,
                                        wx.NamedColour(DOWNLOADED_TEXT_COLOUR))

    def get_selected_programme(self):
        item = self.tree.GetSelection()
        if not item.IsOk():
            return None

        programme = self.tree.GetItemData(item).GetData()
        if hasattr(programme, "episodes"):
            return programme
        else:
            return None

    def delete_programme(self, programme):
        # After deletion, go to the next item
        next_item = self.tree.GetNextSibling(programme.view_item)
        # Or the previous item
        if not next_item.IsOk():
            next_item = self.tree.GetPrevSibling(programme.view_item)
        # Or the parent
        if not next_item.IsOk():
            next_item = self.tree.GetParent(programme.view_item)

        self.tree.Delete(programme.view_item)

        self.tree.SelectItem(next_item)
# end of class ChannelPanel


