#!/usr/bin/env python
import time

class State():

    # TODO Clarify committed, applied, replicated
    # a leader broadcasts every 50ms
    BROADCAST_TIMEOUT = 50

    def __init__(self, server):
        # Persistent State on All Servers
        self.term = 0
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
        # in ms
        self.last_heartbeat = 0

    def prepare_for_application(self):
        self.state = "candidate"
        self.term += 1
        self.vote_count += 1
        self.voted_for = self.server.my_id
        return {"src": self.voted_for, "dst": "FFFF",
                "leader": self.voted_for, "type": "vote", "term": self.term}

    def set_leader(self):
        self.state = "leader"
        # the election is over
        self.__reset_vote_stats()

    def add_vote(self):
        self.vote_count += 1

    def vote(self, msg):
        mess = {"src": self.server.my_id, "dst": msg['leader'],
                "leader": msg['leader'], "type": "vote", "term": msg['term']}
        self.voted_for = msg['leader']
        return mess

    def gen_heartbeat(self, won=False):
        mess = {"src": self.server.my_id, "dst": "FFFF",
                "leader": self.server.my_id, "type": "heart", "term":
                    self.term}
        if won:
            mess["type"] = "won"
        self.last_heartbeat = time.time()*1000
        return mess

    def check_heart(self):
        if self.state=="leader" and \
                ((time.time()*1000) - self.last_heartbeat >
                 State.BROADCAST_TIMEOUT):
            return self.gen_heartbeat()

    def is_follower(self):
        return self.state == "follower"

    def is_candidate(self):
        return self.state == "candidate"

    def is_leader(self):
        return self.state == "leader"

    def go_back_to_follower(self):
        self.state = "follower"
        self.__reset_vote_stats()

    def __reset_vote_stats(self):
        self.vote_count = 0
        self.voted_for = None