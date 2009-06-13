#!/usr/bin/env python

import wx

class Interactor(object):
    """
    This class translates the low level events into the "higher level language" of the presenter
    """
    def install(self, presenter, view):
        self.presenter = presenter
        self.view = view

        view.channel_panel.tree.Bind(wx.EVT_TREE_SEL_CHANGED, 
                                     self._on_channel_change)
        view.channel_panel.tree.Bind(wx.EVT_CHAR, 
                                     self._on_tree_key)
        view.episode_panel.episode_list.Bind(wx.EVT_LISTBOX, 
                                             self._on_episode_change)
#        view.download_list.Bind(EVT_LIST_ITEM_SELECTED

        # Toolbar buttons:
                  
        view.channel_panel.channel_toolbar.Bind(wx.EVT_TOOL, 
                                                self._on_subscribe,
             id=view.channel_panel.channel_toolbar.ID_SUBSCRIBE)

        view.channel_panel.channel_toolbar.Bind(wx.EVT_TOOL, 
                                                self._on_unsubscribe,
             id=view.channel_panel.channel_toolbar.ID_UNSUBSCRIBE)

        view.episode_panel.episode_toolbar.Bind(wx.EVT_TOOL, 
                                                self._on_download,
             id=view.episode_panel.episode_toolbar.ID_DOWNLOAD)

        view.episode_panel.episode_toolbar.Bind(wx.EVT_TOOL, 
                                                self._on_ignore,
             id=view.episode_panel.episode_toolbar.ID_IGNORE)

    def _on_channel_change(self, event):
        programme = self.view.get_selected_programme()
        self.presenter.update_episodes(programme)

    def _on_episode_change(self, event):
        episode = self.view.get_selected_episode()
        self.presenter.on_episode_select(episode)

    def _on_tree_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            self._on_unsubscribe()
        else:
            event.Skip()

    def _on_subscribe(self, event):
        pass

    def _on_unsubscribe(self, event=None):
        programme = self.view.get_selected_programme()
        self.presenter.unsubscribe(programme)

    def _on_download(self, event):
        episode = self.view.episode_panel.get_selected_episode()
        self.presenter.download(episode)

    def _on_ignore(self, event):
        episode = self.view.episode_panel.get_selected_episode()
        self.presenter.ignore(episode)
