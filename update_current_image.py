#!/usr/bin/env python3
#
# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode
#
# Author(s):
#   Tom Parker <tparker@usgs.gov>

""" Retrieve camera images from email attachments."""

import logging
import os
import pathlib
import shutil
import dateutil.parser
from datetime import datetime
import pytz
from PIL import Image

DIR_SUFFIX_FMT = "archive/%Y/%m/%d/%H"
FILENAME_FMT = "%Y%m%d%H%M%SM.jpg"
HST = pytz.timezone('US/Hawaii')
THUMBNAIL_SIZE = (384, 288)


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
    except OSError:
        logger.info("js file not found in %s.", js_file)

    logger.debug("Current image is %s", image_time)
    return image_time


def find_most_recent_image(image_dir):
    most_recent = None
    try:
        suffix = datetime.now(tz=HST).strftime(DIR_SUFFIX_FMT)
        current_dir = image_dir / suffix
        dir_list = os.listdir(current_dir)
        most_recent_file = sorted(dir_list)[-1]
        logger.debug("Most recent file: %s", most_recent_file)
        most_recent = datetime.strptime(most_recent_file, FILENAME_FMT)
        most_recent = HST.localize(most_recent)
        logger.debug("Most recent time: %s", most_recent)
    except OSError:
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

    try:
        im = Image.open(last_file)
        im.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
        thumbnail = image_dir / "M.thumb.jpg"
        im.save(thumbnail, "JPEG")
    except IOError:
        logger.error("cannot create thumbnail for '%s'", last_image)


def update_cam(cam):
    logger.debug("Updating cam %s", cam)
    image_dir = get_image_dir(cam)
    js_file = image_dir / "js.js"
    image_time = get_image_time(js_file)
    logger.debug("Current image time: %s", image_time)
    most_recent_image = find_most_recent_image(image_dir)
    if most_recent_image is None:
        logger.info("No recent image, nothing to do")
        return

    if image_time is None or most_recent_image > image_time:
        write_js(js_file, most_recent_image)
        create_current_image(image_dir, most_recent_image)
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
