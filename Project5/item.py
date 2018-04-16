#!/usr/bin/env python

from json import dumps

class Item:

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def json(self):
        return dumps({'key': self.key, 'value': self.value})
