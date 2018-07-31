#!/usr/bin/env python3
#
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode
#
# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" Retrieve camera images from email attachments."""

from datetime import timedelta, datetime
import logging
import os
import sys
import socket
import struct
import pathlib
from urllib.parse import urlparse
import errno
from multiprocessing import Process
from buffering_smtp_handler import BufferingSMTPHandler
import sys
from imaplib import IMAP4, IMAP4_SSL
import getpass
import email
import email.message
import email.policy
import datetime
import sys
import shutil
import time
import dateutil.parser
from datetime import datetime
import pytz

DIR_SUFFIX_FMT = "archive/%Y/%m/%d/%H"
FILENAME_FMT = "%Y%m%d%H%M%SM.jpg"

def exit_with_error(error):
    logger.error(error)
    logging.shutdown()
    sys.exit(1)


def get_env_var(var, default=None):
    if var in os.environ:
        logger.debug("%s: %s", var, os.environ[var])
        return os.environ[var]

    else:
        if default is None:
            msg = "Envionment variable {} not set, exiting.".format(var)
            exit_with_error(EnvironmentError(msg))
        else:
            logger.debug("%s: %s (default)", var, default)
            return default


def setup_logging():
    global logger
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    logger.addHandler(ch)

    try:
        subject = "camfetcher logs"
        handler = BufferingSMTPHandler(os.environ['MAILHOST'],
                                       os.environ['FF_SENDER'],
                                       os.environ['FF_RECIPIENT'], subject,
                                       1000, "%(levelname)s - %(message)s")
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
    except KeyError:
        logger.info("SMTP logging not configured.")


def get_image_dir(cam):
    base_dir = pathlib.Path(get_env_var('CF_OUT_DIR'))
    image_dir = base_dir / cam / "images"
    logger.debug("image_dir: %s", image_dir)

    return image_dir


def get_image_time(js_file):
    image_time = None
    try:
        with open(js_file, 'r') as f:
            for line in f:
                if "datetime" not in line:
                    continue
                time_str = line.split('"')[1]
                image_time = dateutil.parser.parse(time_str, fuzzy=True,
                                                   tzinfos={"HST": -36000})
    except FileNotFoundError:
        logger.info("js file not found in %s.", js_file)

    logger.debug("Current image is %s", image_time)
    return image_time


def find_most_recent_image(image_dir):
    most_recent = None
    try:
        suffix = time.strftime(DIR_SUFFIX_FMT, time.localtime())
        current_dir = image_dir / suffix
        most_recent_file = os.listdir(current_dir)[-1]
        logger.debug("Most recent file: %s", most_recent_file)
        most_recent = datetime.strptime(most_recent_file, FILENAME_FMT)
        hst = pytz.timezone('US/Hawaii')
        most_recent = hst.localize(most_recent)

        logger.debug("Most recent time: %s", most_recent)
    except FileNotFoundError:
        logger.info("Hour dir not found. (%s)", current_dir)

    return most_recent


def write_js(js_file, image_time):
    with open(js_file, 'w') as f:
        time_fmt = 'var datetime = "%Y-%m-%d %H:%M:%S (HST)";\n'
        f.write(image_time.strftime(time_fmt))
        f.write('var frames   = new Array("M");\n')


def create_current_image(image_dir, last_image):
    logger.debug("writing current image")
    suffix = last_image.strftime(DIR_SUFFIX_FMT)
    filename = last_image.strftime(FILENAME_FMT)
    last_file = image_dir / suffix / filename
    current_file = image_dir / "M.jpg"
    shutil.copyfile(last_file, current_file)


def update_cam(cam):
    logger.debug("Updating %s", cam)
    image_dir = get_image_dir(cam)
    js_file = image_dir / "js.js"
    image_time = get_image_time(js_file)
    logger.debug("Old image time: %s", image_time)
    most_recent = None
    last_image = find_most_recent_image(image_dir)
    if last_image is None:
        logger.info("No recent image, nothing to do")
        return

    if image_time is None or last_image > image_time:
        write_js(js_file, last_image)
        create_current_image(image_dir, last_image)
        logger.info("new image")


def main():
    """Where it all begins."""

    setup_logging()

    for cam in get_env_var('CF_CAMS').split(":"):
        update_cam(cam)

    logger.debug("That's all for now, bye.")
    logging.shutdown()


if __name__ == '__main__':
    main()
