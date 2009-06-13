#!/usr/bin/env python

import wx

class EpisodeList(wx.SimpleHtmlListBox):
    def update(self, programme):
        """ 
        Update the episode list with the selected programme.
        Returns the currently selected episode object.
        """
        self.Clear()
        if programme is None:
            return None

        for episode in programme.episodes:
            self.Append(self._generate_html(episode),
                        clientData=episode)

        # Select the first episode
        self.SetSelection(0)
        return self.GetClientData(0)

    def _generate_html(self, episode):
         if episode.downloaded:
             html = ("<font color=grey>%s</font><br>" % episode.episode +
                     "<table><td>&nbsp;</td><td>" + # Indent
                     "<font color=grey size=-1>%s</font>" % episode.desc +
                     "</td></table>")
         elif episode.ignored:
             html = ("<em><font color=red>%s</font><br>" % episode.episode +
                     "<table><td>&nbsp;</td><td>" + # Indent
                     "<font color=red size=-1>%s</font>" % episode.desc +
                     "</td></table></em>")
         else:
            html = ("<strong>%s</strong><br>" % episode.episode +
                    "<table><td>&nbsp;</td><td>" + # Indent
                    "<font size=-1>%s</font>" % episode.desc +
                    "</td></table>")

         return html

    def get_selected_episode(self):
        """ Returns the episode object for the current selection """
        index = self.GetSelection()
        if index == wx.NOT_FOUND:
            return None
        else:
            return self.GetClientData(index)

    def refresh_selected_episode(self):
        index = self.GetSelection()
        if index == wx.NOT_FOUND:
            return

        episode = self.GetClientData(index)
        self.SetString(index, self._generate_html(episode))

    def select_next_episode(self):
        """ 
        Selects the next episode not marked as "ignored" or "downloaded"
        Returns the selected episode object
        """        
        index = self.GetSelection()
        if index == wx.NOT_FOUND:
            return None

        start_index = index

        while index < self.GetCount():
            episode = self.GetClientData(index)
            if not episode.downloaded and not episode.ignored:
                self.SetSelection(index)
                return self.GetClientData(index)
            index += 1

        return self.GetClientData(start_index)

# end of class EpisodePanel


