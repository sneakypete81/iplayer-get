#!/usr/bin/env python

import pysvn
import sys
import subprocess
import getpass

MNEMOSYNE_SVN_DIR = ".mnemosyne"

def _get_login( realm, username, may_save ):
    new_username = raw_input("Username [%s] >" % username)
    if new_username == "":
        new_username = username
    
    password = getpass.getpass("Password >")
    
    return True, new_username, password, True

def _ssl_server_trust_prompt(trust_dict):
      """ ssl_server_trust_prompt will be called when we need ssl ok
      """
      return True, 0, False

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
    client.callback_get_login = _get_login
    client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
    
    if not is_clean(client):
        raise Exception("Mnemosyne SVN directory not clean.")

    print "Updating mnemosyne database from server...",
    sys.stdout.flush()
    client.update(MNEMOSYNE_SVN_DIR)
    print "Done"

    print "Launching mnemosyne..."
    if sys.platform == "win32":
        subprocess.call("c:\progra~1\mnemosyne\mnemosyne.exe", shell=True)
    else:
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
