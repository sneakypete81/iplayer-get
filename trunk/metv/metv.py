#!/usr/bin/env python

import view
import interactor
import presenter
import channels

def run():
    '''
    Creates the Presenter and connects it to the config and pico_log models,
    the view interface and the interactor
    '''
    presenter.Presenter(channels.Channels(), 
                        view.MeTvFrame(), 
                        interactor.Interactor())

if __name__ == "__main__": 
    run()
