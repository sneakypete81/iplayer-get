# Installing #

  * Make sure you have ruby and python installed

  * Download [iplayer-dl](http://po-ru.com/projects/iplayer-downloader/)

  * Download iplayer-get from the **DOWNLOADS** tab, and unzip it somewhere

  * (optional) Make the script runnable from any directory:
```
sudo ln -s /path/to/iplayer-get.py /usr/bin/iplayer-get
```

To get help:
```
iplayer-get -h
```

# Usage #

## Example ##
```
     > iplayer-get -p ~/movies
     > iplayer-get -a "Doctor Who"
     > iplayer-get -a "Spooks"
     > iplayer-get
```

### Configure the download path ###
```
iplayer-get -p DOWNLOAD_PATH
```
where DOWNLOAD\_PATH is where to download new episodes

### Add a new series ###
```
iplayer-get -a ADD_SERIES
```
where ADD\_SERIES is the name of the series (in quotes if more than one word)

### Download ###
Download new episodes by running iplayer-get with no arguments
```
iplayer-get
```

# How It Works #
For each series registered, iplayer-get goes to the BBC's iplayer search page and searches for the series name. Any matching results are downloaded, provided the series name matches.