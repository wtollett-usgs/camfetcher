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
from imaplib import IMAP4, IMAP4_SSL
import email
import email.message
import email.policy
import socket
import sys
import shutil
import time
import tomputils.util as tutil

REQ_VERSION = (3, 5)
TMP_DIR = "/tmp"

env = None


def get_archive_dir(cam, image_time):
    archive_dir = pathlib.Path(tutil.get_env_var('CF_OUT_DIR'))
    archive_dir /= time.strftime(cam + "/images/archive/%Y/%m/%d/%H",
                                 image_time)

    if not os.path.exists(archive_dir):
        logger.info("Creating directory: %s", archive_dir)
        os.makedirs(archive_dir)

    return archive_dir


def process_email(msg, cam):
    for attchment in msg.iter_attachments():
        filename = attchment.get_filename()
        if filename is None:
            continue

        tmp_file = os.path.join(TMP_DIR, filename)
        logger.debug("creating %s", tmp_file)
        fp = open(tmp_file, 'wb')
        fp.write(attchment.get_payload(decode=True))
        fp.close()

        file_time_str = filename.split('_')[1]
        try:
            image_time = time.strptime(file_time_str, "%Y%m%d%H%M%S")
        except ValueError:
            logger.exception("Unable to parse filename.")

        archive_dir = get_archive_dir(cam, image_time)
        archive_file = archive_dir / (file_time_str + "M.jpg")

        shutil.move(tmp_file, archive_file)


def process_mailbox(M, cam):
    rv, msgs = M.search(None, "UNSEEN")
    if rv != 'OK':
        logger.debug("No new messages found for cam %s.", cam)
        return

    for msgNum in msgs[0].split():
        rv, data = M.fetch(msgNum, '(RFC822)')

        if rv != 'OK':
            logger.error("Cannot retrieve message %s for cam %s", msgNum, cam)
            return

        msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
        process_email(msg, cam)


def check_version():
    if sys.version_info < REQ_VERSION:
        msg = "Python interpreter is too old. I need at least 3.5 " \
              + "for EmailMessage.iter_attachments() support."
        tutil.exit_with_error(msg)


def main():
    """Where it all begins."""

    global logger
    logger = tutil.setup_logging("camfetchers errors")
    check_version()

    if 'CF_TIMEOUT' in os.environ:
        timeout = float(os.environ['CF_TIMEOUT'])
        logger.debug("Setting timeout to %.2f" % timeout)
        socket.setdefaulttimeout(timeout)

    with IMAP4_SSL(tutil.get_env_var('IMAPSERVER')) as M:
        try:
            M.login(tutil.get_env_var('CF_USER'),
                    tutil.get_env_var('CF_PASSWD'))
        except IMAP4.error:
            tutil.exit_with_error("Login failed.")

        for cam in tutil.get_env_var('CF_CAMS').split(':'):
            rv, data = M.select(cam)
            if rv == 'OK':
                logger.debug("Processing mailbox %s", cam)
                process_mailbox(M, cam)
            else:
                msg = "Received non-OK response opening mailbox %s, " \
                      + "lets skip this one. (%s)"
                logger.error(msg.format(cam, rv))

    logger.debug("That's all for now, bye.")
    logging.shutdown()


if __name__ == '__main__':
    main()
