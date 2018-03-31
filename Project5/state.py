#!/usr/bin/env python


class State:

    # TODO Clarify committed, applied, replicated

    def __init__(self):
        # Persistent State on All Servers
        self.current_term = 0
        # candidate ID
        self.voted_for = None
        # a list of Entry objects
        self.log = []

        # Volatile State on All Servers
        # index of highest log entry that was committed
        self.commit_index = 0
        # index of highest log entry that was applied to state machine
        self.last_applied = 0

        # Volatile State on Leaders
        # server -> index of next log entry to send to that server
        # TODO initialize to current last log entry + 1 => need to know servers
        self.next_index = {}
        # server -> highest log entry known to be replicated on the server
        self.match_index = {}