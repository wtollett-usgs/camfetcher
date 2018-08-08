# camfetcher

[![Build Status](https://travis-ci.org/tparker-usgs/camfetcher.svg?branch=master)](https://travis-ci.org/tparker-usgs/camfetcher)
[![Code Climate](https://codeclimate.com/github/tparker-usgs/camfetcher/badges/gpa.svg)](https://codeclimate.com/github/tparker-usgs/camfetcher)

## Configuration

camfetcher looks to its environment for configuration. It requires the following four environment variables to be set:

  * **IMAPSERVER** remote server hosting mailboxes to be polled
  * **CF_USER** Usename used to connect to IMAPSERVER
  * **CF_PASSWD** Password used to connect to IMAPSERVER
  * **CF_CAMS** A colon-seperated list of mailboxes to poll for images
  * **CF_OUT_DIR** Base directory. Images will be placed here.

Optionally, camfetcher will email messages logged at level error or greater. To enable this, set the following environment variables:
  * **MAILHOST** SMTP server
  * **LOG_SENDER** Address used for From:
  * **LOG_RECIPIENT** Address used for To:
  
## Installation
camfetcher can be installed directly or run in a Docker container. 

To install directly, place the two .py files somethere convienent and install the required Python libs with something like `pip install -r requirements.txt`.

The `support/` directory has example files for building a docker image. Start with `support/deploy.sh` and go from there.

## Operation

### camfetcher.py
camfetcher.py does the work of retrieving the images. When launched, camfetcher.py will connect to the remote IMAP server and download all unread messages in the folders pointed to by the *CF_CAMS* environment variable. Each message will be searched for attachements and those with a filename matching the Spartan standard will be downloaded and placed into a directory structure suitable for long-term storage. 

### update_current_image.py
update_current_image.py writes metadata for the most recent image, creates a copy of that image at a well-known location, and also creates a thumbnail of the image.

When launched, update_current_image.py will work through camera-specific directories for cams pointed to by the *CF_CAMS* environment variable. It will read the current metadata file and look for an image uploaded in the current hour that is more recent than indicated in that file. If one is found, the metadata file, image copy, and thumbnail will all be updated.
