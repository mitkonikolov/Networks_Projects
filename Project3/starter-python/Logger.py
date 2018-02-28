#!/usr/bin/python -u
import sys
import datetime


class Logger(object):

    def log_data(self, string):
        sys.stdout.write(string)

    def log(self, string):
        sys.stderr.write("{} [DEBUG] {}\n".format(datetime.datetime.now().strftime("%H:%M:%S.%f"),
                                                  string))
