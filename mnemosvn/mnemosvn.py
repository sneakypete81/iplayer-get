#!/usr/bin/env python

import pysvn
import sys
import subprocess

MNEMOSYNE_SVN_DIR = ".mnemosyne"

def is_clean(client):
    """ Ensure that mnemosyne svn directory is completely clean """
    abnormal_files = [item for item in client.status(MNEMOSYNE_SVN_DIR)
                      if item.text_status != pysvn.wc_status_kind.normal]
    return abnormal_files == []

def add_unversioned(client):
    """ Add any unversioned files """
    new_files = [item.path for item in client.status(MNEMOSYNE_SVN_DIR)
                 if item.text_status == pysvn.wc_status_kind.unversioned]
    client.add(new_files)

def remove_missing(client):
    """ Remove any missing files """
    missing_files = [item.path for item in client.status(MNEMOSYNE_SVN_DIR)
                     if item.text_status == pysvn.wc_status_kind.missing]
    client.remove(missing_files)

def run():
    client = pysvn.Client()
    
    if not is_clean(client):
        raise Exception("Mnemosyne SVN directory not clean.")

    print "Updating mnemosyne database from server...",
    sys.stdout.flush()
    client.update(MNEMOSYNE_SVN_DIR)
    print "Done"

    print "Launching mnemosyne..."
    subprocess.call("mnemosyne", shell=True)

    add_unversioned(client)
    remove_missing(client)

    print "Writing changes to server...",
    sys.stdout.flush()
    # Commit all changes
    client.checkin(MNEMOSYNE_SVN_DIR, "mnemosvn.py autocheckin")
    print "Done"

    if not is_clean(client):
        raise Exception("Mnemosyne SVN directory not clean.")


if __name__ == "__main__":
    run()
