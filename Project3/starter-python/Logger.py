#!/usr/bin/python -u
import sys
import datetime

class Logger(object):
    def log(self, string):
        sys.stderr.write(datetime.datetime.now().strftime(
            "%H:%M:%S.%f") + " " + string + "\n")