#!/usr/bin/env python

import wx

class Interactor(object):
    """
    This class translates the low level events into the "higher level language" of the presenter
    """
    def install(self, presenter, view):
        self.presenter = presenter
        self.view = view

        view.Bind(wx.EVT_CLOSE, self._on_app_close)

        view.channel_tree.Bind(wx.EVT_TREE_SEL_CHANGED, 
                               self._on_channel_change)
        view.channel_tree.Bind(wx.EVT_CHAR, 
                               self._on_tree_key)
        view.channel_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED,
                               self._on_tree_doubleclick)
        view.episode_list.Bind(wx.EVT_LISTBOX, 
                               self._on_episode_change)
        view.download_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                                self._on_download_doubleclick)
        # Toolbar buttons:
                  
        view.channel_toolbar.Bind(wx.EVT_TOOL, 
                                  self._on_subscribe,
                                  id=view.channel_toolbar.ID_SUBSCRIBE)

        view.channel_toolbar.Bind(wx.EVT_TOOL, 
                                  self._on_unsubscribe,
                                  id=view.channel_toolbar.ID_UNSUBSCRIBE)

        view.episode_toolbar.Bind(wx.EVT_TOOL, 
                                  self._on_download,
                                  id=view.episode_toolbar.ID_DOWNLOAD)

        view.episode_toolbar.Bind(wx.EVT_TOOL, 
                                  self._on_ignore,
                                  id=view.episode_toolbar.ID_IGNORE)

        # Subscriptions Dialog:

        view.subscriptions_dialog.notebook.Bind(wx.EVT_BUTTON,
                                                self._on_subscriptions_button)

    def _on_app_close(self, event):
        self.presenter.on_close(event)

    def _on_channel_change(self, event):
        programme = self.view.channel_tree.get_selected_programme()
        self.presenter.update_episodes(programme)

    def _on_episode_change(self, event):
        episode = self.view.episode_list.get_selected_episode()
        self.presenter.on_episode_select(episode)

    def _on_tree_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            self._on_unsubscribe()
        else:
            event.Skip()

    def _on_tree_doubleclick(self, event):
        channel = self.view.channel_tree.get_selected_channel()
        self.presenter.show_channel_log(channel)

    def _on_subscribe(self, event):
        self.presenter.show_subscriptions_dialog()

    def _on_unsubscribe(self, event=None):
        programme = self.view.channel_tree.get_selected_programme()
        self.presenter.unsubscribe(programme)

    def _on_download(self, event):
        episode = self.view.episode_list.get_selected_episode()
        self.presenter.download(episode)

    def _on_ignore(self, event):
        episode = self.view.episode_list.get_selected_episode()
        self.presenter.ignore(episode)

    def _on_download_doubleclick(self, event):
        episode = self.view.download_list.get_selected_episode()
        self.presenter.show_download_log(episode)

# Subscriptions Dialog
######################

    def _on_subscriptions_button(self, event):
        pane = event.GetEventObject().GetParent()
        channel = pane.channel
        
        if event.GetEventObject() == pane.show_button:
            programmes = pane.hidden_list.get_selected_programmes()
            self.presenter.subscriptions_subscribe(channel, programmes)
        else:
            programmes = pane.subscribed_list.get_selected_programmes()
            self.presenter.subscriptions_unsubscribe(channel, programmes)
