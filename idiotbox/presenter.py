#!/usr/bin/env python
from wx.lib.pubsub import Publisher

class Presenter(object):
    """
    This is the object that takes care of the logic of your application.
    It also creates a "higher level language" in which you express what happens 
    inside your application.
    """
    def __init__(self, channels, view, interactor):
        self.channels = channels
        self.view = view

        interactor.install(self, view)

        Publisher().subscribe(self._msg_refresh_complete, 
                              channels.TOPIC_REFRESH_COMPLETE)
        Publisher().subscribe(self._msg_refresh_error, 
                              channels.TOPIC_REFRESH_ERROR)
        Publisher().subscribe(self._msg_download_progress, 
                              channels.downloader.TOPIC_DOWNLOAD_PROGRESS)
        Publisher().subscribe(self._msg_download_complete, 
                              channels.downloader.TOPIC_DOWNLOAD_COMPLETE)
#         Publisher().subscribe(self._msg_download_error, 
#                               channels.downloader.TOPIC_DOWNLOAD_ERROR)

        channels.refresh_all()

        view.channel_tree.clear()
        for channel in channels:
            view.channel_tree.add(channel)

        view.download_list.set_downloader(channels.downloader)
        view.start()

    def on_close(self, event):
        # Make sure we first shut down any processes & save our settings
        self.channels.shutdown()
        self.view.Destroy()

    def _msg_refresh_complete(self, message):
        """ Called when a channel refresh is completed """
        channel = message.data
        channel.parse_cache()
        self.view.channel_tree.update(channel)
        if channel.title in self.view.subscriptions_dialog.panes:
            self.view.subscriptions_dialog.panes[channel.title].update()

    def _msg_refresh_error(self, message):
        """ Called when a channel refresh is completed """
        channel = message.data
        self.view.channel_tree.update(channel)

    def _msg_download_progress(self, message):
        self.view.download_list.update()
        if self.view.download_log is not None:
            self.view.download_log.update()

    def _msg_download_complete(self, message):
        self.view.download_list.update()
        episode = message.data
        episode.channel_obj.mark_downloaded(episode)

    def update_episodes(self, programme):
        """ Called when a programme is selected in the left panel """
        self.view.episode_list.update(programme)
        episode = self.view.episode_list.select_next_episode()
        self.view.episode_toolbar.update(episode)

    def on_episode_select(self, episode):
        self.view.episode_toolbar.update(episode)

    def unsubscribe(self, programme):
        """ Call to unsubscribe from the specified programme """
        if programme is not None:
            programme.channel_obj.unsubscribe(programme)
            self.view.channel_tree.delete_programme(programme)

    def play(self, episode):
        if episode is not None:
            self.channels.streamer.stream(episode)
            episode.channel_obj.mark_downloaded(episode)

            self.view.episode_list.refresh_selected_episode()
            self.view.channel_tree.refresh_selected_programme()
            episode = self.view.episode_list.select_next_episode()
            self.view.episode_toolbar.update(episode)

    def download(self, episode):
        """ Call to add an episode to the download queue """
        if episode is not None:
            self.channels.downloader.add_episode(episode)
            self.view.download_list.update()

            self.view.episode_list.refresh_selected_episode()
            self.view.channel_tree.refresh_selected_programme()
            episode = self.view.episode_list.select_next_episode()
            self.view.episode_toolbar.update(episode)

    def ignore(self, episode):
        """ Call to add an episode to the list of downloaded episodes """
        if episode is None:
            # Ensure the ignore toolbar button doesn't get set
            self.view.episode_toolbar.update(None)
        else:
            episode.channel_obj.ignore(episode)

            self.view.episode_list.refresh_selected_episode()
            self.view.channel_tree.refresh_selected_programme()
            episode = self.view.episode_list.select_next_episode()
            self.view.episode_toolbar.update(episode)

# Download Log
##############

    def show_download_log(self, episode):
        if episode is not None:
            self.view.show_download_log(episode)

    def show_channel_log(self, channel):
        if channel is not None:
            self.view.show_channel_log(channel)

# Subscriptions Dialog
######################

    def show_subscriptions_dialog(self):
        self.view.show_subscriptions_dialog(self.channels)

    def subscriptions_subscribe(self, channel, programmes):
        # Add to subscribed programmes list if default is to hide
        if channel.channel_settings.require_subscription:
            channel.channel_settings.subscribed_programmes.extend(programmes)
        
        for programme in programmes:
            if programme in channel.channel_settings.unsubscribed_programmes:
                channel.channel_settings.unsubscribed_programmes. \
                    remove(programme)

            if programme in channel.all_programmes:
                del channel.unsubscribed_programmes[programme]
                channel.subscribed_programmes[programme] = \
                    channel.all_programmes[programme]

        self.view.channel_tree.update(channel)
        if channel.title in self.view.subscriptions_dialog.panes:
            pane = self.view.subscriptions_dialog.panes[channel.title]
            pane.hidden_list.clear_selection()
            pane.update()
            pane.subscribed_list.select_programmes(programmes)

    def subscriptions_unsubscribe(self, channel, programmes):
        # Add to unsubscribed programmes list if default is to show
        if not channel.channel_settings.require_subscription:
            channel.channel_settings.unsubscribed_programmes.extend(programmes)

        for programme in programmes:
            if programme in channel.channel_settings.subscribed_programmes:
                channel.channel_settings.subscribed_programmes. \
                    remove(programme)

            if programme in channel.all_programmes:
                del channel.subscribed_programmes[programme]
                channel.unsubscribed_programmes[programme] = \
                    channel.all_programmes[programme]

        self.view.channel_tree.update(channel)
        if channel.title in self.view.subscriptions_dialog.panes:
            pane = self.view.subscriptions_dialog.panes[channel.title]
            pane.subscribed_list.clear_selection()
            pane.update()
            pane.hidden_list.select_programmes(programmes)
