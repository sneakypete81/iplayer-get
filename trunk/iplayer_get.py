#!/usr/bin/env python
#
# Note: seriess is the plural of series (singular)!
#

import os
import subprocess
import commands
import pickle
import urllib
import HTMLParser
import textwrap
import optparse

class Episode():
    def allAttributesExist(self):
        try:
            self.id
            self.series
            self.title
            self.description
            return True
        except:
            return False

class Series():
    SEARCH_URL = "http://www.bbc.co.uk/iplayer/search/tv/"
    LOG_FILE = ".iplayer_dl_log"
    
    def __init__(self, name):
        self.name = name
        self.downloadedEpisodes = []
 
    def __str__(self):
        return "<Series name='%s'>" % self.name
 
    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def hasDownloadedEpisode(self, id):
        return self.downloadedEpisodes.count(id) > 0
    
    def hasNewEpisode(self, id):
        episodes = self.getEpisodes()
        return [ep.id for ep in episodes].count(id) > 0

    def downloadNewEpisodes(self, downloadPath):
        # Ignore results where the series name doesn't match
        episodes = [episode for episode in self.getNewEpisodes()
                    if episode.series.lower() == self.name.lower()]

        for episode in episodes:
            cmd = "iplayer-dl -d %s %s" % (downloadPath, episode.id)

            # iplayer-dl outputs everything to stderr!
            # Redirect to stdout, then tee it off to the logfile
            status = os.system("(%s 2>&1) | tee %s" % (cmd, self.LOG_FILE))
            f=open(self.LOG_FILE)
            output = f.read()
            
            if status == 0 and output.strip().endswith("100.0%"):
                print "Download complete."
                self.downloadedEpisodes.append(episode.id)
            elif status == 0:
                print "*** ERROR: iplayer-dl didn't say '100.0%'"
            else:
                print "*** ERROR: iplayer-dl returned status %d" % status
            
    def getNewEpisodes(self):
        currentEpisodes = self.getEpisodes()
        return [ep for ep in currentEpisodes
                if not self.hasDownloadedEpisode(ep.id)]       

    def getEpisodes(self):
        params = urllib.urlencode({'q': self.name})
        file=urllib.urlopen(self.SEARCH_URL+"?%s" % params)

        parser = SeriesParser()
        parser.feed(file.read())
        return parser.episodes

class IPlayer():
    OPTIONS_FILE = os.path.expanduser("~/.iplayer-get")
    def __init__(self):
        self.seriess = []
        self.downloadPath = os.path.expanduser("~")
        try:
            file = open(self.OPTIONS_FILE, "r")
            self.seriess = pickle.load(file)
            self.downloadPath = pickle.load(file)
        except:
            pass
        
    def __del__(self):
        file = open(self.OPTIONS_FILE, "w")
        pickle.dump(self.seriess, file)
        pickle.dump(self.downloadPath, file)
        
    def addSeries(self, name):
        series = Series(name)
        self.seriess.append(series)

    def delSeries(self, name):
        try:
            self.seriess.remove(Series(name))
            return True
        except:
            return False

    def numSeries(self):
        return len(self.seriess)

    def listSeries(self):
        if len(self.seriess) == 0:
            print "Series list is empty."
            return
        
        for series in self.seriess:
            print "*******************"
            print "Series '%s':" % series.name
            for episode in series.getNewEpisodes():
                if episode.series.lower() != series.name.lower():
                    print "  (%s)" % episode.series
                else:
                    print "  %s: (%s)" % (episode.title, episode.id)
                    print "      %s" % textwrap.fill(episode.description, 60,
                                                     subsequent_indent="      ")
    
    def markDownloaded(self, id):
        for series in self.seriess:
            if series.hasDownloadedEpisode(id):
                return True
            if series.hasNewEpisode(id):
                series.downloadedEpisodes.append(id)
                return True
        return False

    def downloadNewEpisodes(self):
        for series in self.seriess:
            print "Checking series %s..." % series.name
            series.downloadNewEpisodes(self.downloadPath)

class SeriesParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.episodes = []
        self.inEpisodeRow = False
        self.inSeTitle = False
        self.inDescription = False

#    def feed(self, data):
#        print data
        
    def handle_starttag(self, tag, attrs):
        self.inSeTitle = False
        if tag == "tr":
            cls = self.extract_attribute(attrs, "class")
            if cls and cls.find("episode") > -1:
                self.inEpisodeRow = True
                self.episode = Episode()
        
        if self.inEpisodeRow:
            if tag == "a":
                if self.extract_attribute(attrs, "class") == "play-video":
                    href = self.extract_attribute(attrs, "href")
                    parts = href.split("/")
                    id = parts[parts.index("episode")+1]
                    self.episode.id = id
    
            elif tag == "h3":
                if self.extract_attribute(attrs, "class") == "summary":
                    title = self.extract_attribute(attrs, "title")
                    self.episode.title = title
    
            elif tag == "span":
                if self.extract_attribute(attrs, "class") == "se-title":
                    self.inSeTitle = True
                    
            elif tag == "div":
                if self.extract_attribute(attrs, "class") == "description":
                    self.inDescription = True
                    self.episode.description = ""

    def handle_data(self, data):
        if self.inSeTitle:
            self.episode.series = data
        
        elif self.inDescription:
            self.episode.description += data

    def handle_endtag(self, tag):
        self.inSeTitle = False
        if tag == "tr" and self.inEpisodeRow:
            if self.episode.allAttributesExist():
                self.episodes.append(self.episode)
            self.inEpisodeRow = False
        
        elif tag == "div" and self.inDescription:
            self.inDescription = False
    
    def extract_attribute(self, attrs, attribute):
        for attr in attrs:
            if attr[0] == attribute:
                return attr[1]

#####################################

def parseOptions():
    parser = optparse.OptionParser()
    parser.add_option("-a", "--add",
                      dest="add_series",
                      help="Add ADD_SERIES to the list of series to download")
    parser.add_option("-d", "--delete",
                      dest="del_series",
                      help="Delete DEL_SERIES from the list of series to download")
    parser.add_option("-l", "--list",
                      action="store_true", dest="list",
                      help="List new episodes for each series in the scan list")
    parser.add_option("-m", "--mark-as-downloaded",
                      dest="mark_downloaded_id",
                      help="Prevent MARK_DOWNLOADED_ID from being downloaded in the future")
    parser.add_option("-p", "--download-path",
                      dest="download_path",
                      help="Download episodes to DOWNLOAD_PATH")
    (options, args) = parser.parse_args()
    
    if args:
        parser.error("Unexpected argument: '%s'" % args[0])

    return (parser, options)

#######################################

(parser, options) = parseOptions()
done_something = False
iplayer = IPlayer()

if options.download_path:
    iplayer.downloadPath = options.download_path
    print "Episode download path set to '%s'." % options.download_path
    done_something = True

if options.add_series:
    iplayer.addSeries(options.add_series)
    print "Series '%s' added." % options.add_series
    done_something = True

if options.del_series:
    if iplayer.delSeries(options.del_series):
        print "Series '%s' will no longer be downloaded." % options.del_series
    else:
        parser.error("Series '%s' not found" % options.del_series)
    done_something = True

if options.mark_downloaded_id:
    if iplayer.markDownloaded(options.mark_downloaded_id):
        print "Episode ID %s will not be downloaded." % options.mark_downloaded_id
    else:
        parser.error("ID %s not found" % options.mark_downloaded_id)
    done_something = True

if options.list:
    iplayer.listSeries()
    done_something = True

# If nothing else is specified, check for new episodes
if not done_something:
    if iplayer.numSeries() == 0:
        print "Series list is empty."
        parser.print_help()
        exit(1)
    
    iplayer.downloadNewEpisodes()

# Here's an example of a search result table row:
###################################################
# <tr class="episode single-ep"><td class="first">
# <a href="/iplayer/episode/b00ftvvc/Spooks_Series_7_Episode_3/" class="image">
# <img src="http://www.bbc.co.uk/iplayer/images/episode/b00ftvvc_86_48.jpg" width="86" height="48" alt="Spooks: Episode 3" />
# </a></td><td><div class="summary-and-time">
# <a class="play-video" href="/iplayer/episode/b00ftvvc/Spooks_Series_7_Episode_3/">
# <span>Play video - Spooks - Episode 3</span></a><div class="info-wrapper">
# <h3 class="summary" title="Spooks - Episode 3">
# <a class="uid url" href="/iplayer/episode/b00ftvvc/Spooks_Series_7_Episode_3/">
# <span class="se-title">Spooks<span class="blq-hide">-</span></span>
# <span class="ep-title">Episode 3</span></a></h3></div></div></td>
# <td class="last"><div class="details">
# <span class="se-title">Spooks<span class="blq-hide"> - </span></span>
# <span class="ep-title">
# <a class="uid url" href="/iplayer/episode/b00ftvvc/Spooks_Series_7_Episode_3/">
# Episode 3</a></span><div class="description">
# <p>Drama series about the British Security Service. Lucas reveals that the
# Russians interrogated him about Operation Sugar Horse, the most secret
# ongoing spy operation MI5 ever had.</p></div></div></td></tr>
