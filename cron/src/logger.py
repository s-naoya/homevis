#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import smtplib
import traceback
from email.mime.text import MIMEText
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG, INFO


class Logger:
    def __init__(self, name=__name__):
        self.name = name
        self.logger = getLogger(name)
        self.logger.setLevel(INFO)
        formatter = Formatter(
            "%(asctime)s %(process)d %(name)s %(levelname)s %(message)s"
        )

        # stdout
        handler = StreamHandler()
        handler.setLevel(INFO)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # # file
        # handler = handlers.RotatingFileHandler(
        #     filename='your_log_path.log',
        #     maxBytes=1048576,
        #     backupCount=3
        # )
        # handler.setLevel(DEBUG)
        # handler.setFormatter(formatter)
        # self.logger.addHandler(handler)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
        self.__exc_notification(msg)

    def critical(self, msg):
        self.logger.critical(msg)
        self.__exc_notification(msg)

    def __exc_notification(self, msg):
        message = str(time.asctime()) + " " + str(os.getpid()) + \
            "\n" + msg + "\n\n" + traceback.format_exc()
        self.__mail(message)

    def __mail(self, msg):
        mail = MIMEText(msg, "plain")
        mail["Subject"] = "["+self.name+"] Error notification"
        mail["To"] = os.environ["SMTP_TO_ADDRESS"]
        mail["From"] = os.environ["SMTP_FROM_ADDRESS"]

        server = smtplib.SMTP(
            os.environ["SMTP_SERVER"], os.environ["SMTP_PORT"])
        server.send_message(mail)
        server.quit()
