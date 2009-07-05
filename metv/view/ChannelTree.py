#!/usr/bin/env python

import wx
import operator

NORMAL_TEXT_COLOUR = "BLACK"
REFRESH_TEXT_COLOUR = "DIM GREY"
ERROR_TEXT_COLOUR = "RED"
DOWNLOADED_TEXT_COLOUR = "DIM GREY"

class ChannelTree(wx.TreeCtrl):

    def clear(self):
        """ Remove all data from the tree """
        self.DeleteAllItems()
        self.AddRoot(text="")

    def add(self, channel):
        """ Add a new channel to the tree """
        item = self.AppendItem(parent=self.GetRootItem(),
                               text=channel.title,
                               data=wx.TreeItemData(channel))
        self.SetItemBold(item)
        channel.view_item = item
        self.update(channel)
        self.Expand(item)

    def update(self, channel):
        """ Update the tree data for the specified channel """
        channel_item = channel.view_item
        self.DeleteChildren(channel_item)
        if channel.is_refreshing:
            refresh_text = self.AppendItem(parent=channel_item,
                                           text="Refreshing...")
            self.SetItemTextColour(refresh_text, 
                                   wx.NamedColour(REFRESH_TEXT_COLOUR))
        elif channel.error_message is not None:
            refresh_text = self.AppendItem(parent=channel_item,
                                           text="ERROR: %s" % 
                                           channel.error_message)
            self.SetItemTextColour(refresh_text, 
                                   wx.NamedColour(ERROR_TEXT_COLOUR))
        else:
            programmes = channel.subscribed_programmes.values()
            programmes.sort(key=operator.attrgetter('name'))
            for programme in programmes:
                item = self.AppendItem(parent=channel_item,
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
                    self.SetItemTextColour(programme.view_item,
                                           wx.NamedColour(NORMAL_TEXT_COLOUR))
                    return
            # Programme contains only downloaded or ignored episodes
            self.SetItemTextColour(programme.view_item,
                                   wx.NamedColour(DOWNLOADED_TEXT_COLOUR))

    def get_selected_programme(self):
        item = self.GetSelection()
        if not item.IsOk():
            return None

        programme = self.GetItemData(item).GetData()
        if hasattr(programme, "episodes"):
            return programme
        else:
            return None

    def delete_programme(self, programme):
        # After deletion, go to the next item
        next_item = self.GetNextSibling(programme.view_item)
        # Or the previous item
        if not next_item.IsOk():
            next_item = self.GetPrevSibling(programme.view_item)
        # Or the parent
        if not next_item.IsOk():
            next_item = self.GetParent(programme.view_item)

        self.Delete(programme.view_item)
        self.SelectItem(next_item)


