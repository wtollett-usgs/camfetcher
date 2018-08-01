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
from buffering_smtp_handler import BufferingSMTPHandler
from imaplib import IMAP4, IMAP4_SSL
import email
import email.message
import email.policy
import sys
import shutil
import time


REQ_VERSION = (3, 5)
env = None


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


def get_out_dir(cam, image_time):
    out_dir = pathlib.Path(get_env_var('CF_OUT_DIR'))
    out_dir /= time.strftime(cam + "/images/archive/%Y/%m/%d/%H", image_time)

    if not os.path.exists(out_dir):
        logger.info("Creating directory: %s", out_dir)
        os.makedirs(out_dir)

    return out_dir


def process_email(msg, cam):
    for attchment in msg.iter_attachments():
        filename=attchment.get_filename()
        if filename is None:
            continue

        sv_path = os.path.join("/tmp", filename)
        if not os.path.isfile(sv_path):
            logger.debug("creating %s", sv_path)
            fp = open(sv_path, 'wb')
            fp.write(attchment.get_payload(decode=True))
            fp.close()

        file_time_str = filename[9:23]
        image_time = time.strptime(file_time_str, "%Y%m%d%H%M%S")
        out_dir = get_out_dir(cam, image_time)
        out_file = out_dir / (file_time_str + "M.jpg")

        shutil.move(sv_path, out_file)


def process_mailbox(M, cam):
    rv, msgs = M.search(None, "UNSEEN")
    if rv != 'OK':
        logger.debug("No messages found!")
        return

    for num in msgs[0].split():
        rv, data = M.fetch(num, '(RFC822)')

        if rv != 'OK':
            logger.error("Cannot retrieve message %s", num)
            return

        msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
        process_email(msg, cam)


def check_version():
    if sys.version_info < REQ_VERSION:
        msg = "Python interpreter is too old. I need at least 3.5 " \
              + "for EmailMessage.iter_attachments() support."
        exit_with_error(msg)


def main():
    """Where it all begins."""

    setup_logging()
    check_version()

    with  IMAP4_SSL(get_env_var('IMAPSERVER')) as M:
        try:
            M.login(get_env_var('CF_USER'),
                    get_env_var('CF_PASSWD'))
        except IMAP4.error:
            exit_with_error("Login failed.")

        for cam in get_env_var('CF_CAMS').split(':'):
            rv, data = M.select(cam)
            if rv == 'OK':
                logger.debug("Processing mailbox %s", cam)
                process_mailbox(M, cam)
                M.close()

    logger.debug("That's all for now, bye.")
    logging.shutdown()


if __name__ == '__main__':
    main()
