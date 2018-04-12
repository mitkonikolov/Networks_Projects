#!/usr/bin/env python


class State:

    # TODO Clarify committed, applied, replicated

    def __init__(self, server):
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

        # state can be leader, follower, candidate
        self.state = "follower"

        self.server = server
        self.vote_count = 0

    def prepare_for_application(self):
        self.state.state = "candidate"
        self.current_term += 1
        self.vote_count += 1
        self.voted_for = self.server.my_id
        return {"src": self.voted_for, "dst": "FFFF", "leader": self.voted_for, "type": "vote"}
