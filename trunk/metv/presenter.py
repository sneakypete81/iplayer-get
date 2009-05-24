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

        Publisher().subscribe(self._msg_refresh_complete, channels.TOPIC_REFRESH_COMPLETE)
        Publisher().subscribe(self._msg_refresh_error, channels.TOPIC_REFRESH_ERROR)

        channels.refresh_all()

        view.delete_all_channels()
        for channel in channels:
            view.add_channel(channel)
        view.start()

    def _msg_refresh_complete(self, message):
        """ Called when a channel refresh is completed """
        channel = message.data
        channel.parse_cache()
        self.view.update_channel(channel)

    def _msg_refresh_error(self, message):
        """ Called when a channel refresh is completed """
        channel = message.data
        self.view.update_channel(channel)

    def update_episodes(self, programme):
        """ Called when a programme is selected in the left panel """
        self.view.update_episodes(programme)

    def unsubscribe(self, programme):
        """ Call to unsubscribe from the specified programme """
        if programme is not None:
            programme.channel.unsubscribe(programme)
            self.view.delete_programme(programme)

    def download(self, episode):
        """ Call to add an episode to the download queue """
        if episode is not None:
            print "download"

    def ignore(self, episode):
        """ Call to add an episode to the list of ignored episodes """
        if episode is not None:
            print "ignore"
