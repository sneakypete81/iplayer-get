#!/usr/bin/env python
import wx
import wx.lib.mixins.listctrl as listmix

NO_EMPHASIS_TEXT_COLOUR = "DIM GREY"

class SubscriptionsList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, "")
        self.programmes = []
        self.no_emphasis_attr = wx.ListItemAttr()
        self.no_emphasis_attr.SetTextColour(NO_EMPHASIS_TEXT_COLOUR)

    def update(self, programmes, emphasis=None):
        self.programmes = programmes
        self.programmes.sort()
        self.emphasis = emphasis

        count = len(programmes)
        self.SetItemCount(count)
        self.RefreshItems(0, count-1)

    def get_selected_programmes(self):
        selected_programmes = []
        item = self.GetNextItem(wx.NOT_FOUND,
                                wx.LIST_NEXT_ALL,
                                wx.LIST_STATE_SELECTED);
        while item != wx.NOT_FOUND:
            selected_programmes.append(self.programmes[item])
            item = self.GetNextItem(item,
                                    wx.LIST_NEXT_ALL,
                                    wx.LIST_STATE_SELECTED);
        return selected_programmes

    def select_programmes(self, programmes):
        for programme in programmes:
            if programme in self.programmes:
                item = self.programmes.index(programme)
                print "select %s" % programme
                self.SetItemState(item, state=wx.LIST_STATE_SELECTED,
                                  stateMask=wx.LIST_STATE_SELECTED)

    def clear_selection(self):
        item = self.GetNextItem(wx.NOT_FOUND,
                                wx.LIST_NEXT_ALL,
                                wx.LIST_STATE_SELECTED);
        while item != wx.NOT_FOUND:
            self.SetItemState(item, state=0, stateMask=wx.LIST_STATE_SELECTED)
            item = self.GetNextItem(item,
                                    wx.LIST_NEXT_ALL,
                                    wx.LIST_STATE_SELECTED);


    def OnGetItemText(self, item, col):
        return self.programmes[item]

    def OnGetItemAttr(self, item):
        if self.emphasis == None or self.programmes[item] in self.emphasis:
            # Use default attributes
            return None
        else:
            return self.no_emphasis_attr
                                   
