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

        self.num_commits = 0

        # dictionary storing
        self.dict = {}

        self.indexes = {}

        self.prevLogIndex = -1
        self.prevLogTerm = None
        self.LogIndex = 0
        self.LogTerm = None
        self.entries = []
        self.num_commits = {}
        self.prepared_message = {}
        self.leaderCommit = 0

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
        self.index_set()
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

    def redirect_to_leader(self, msg):
        mess = {"src": self.server.my_id, "dst": msg['src'],
                "leader":self.server.leader, "type": "redirect", "MID": msg['MID']}
        return mess

    def get_value(self, msg):
        mess = {"src": self.server.my_id, "dst": msg['src'],
                "leader": self.server.leader, "type": "ok", "MID": msg['MID'],
                "value": self.dict[msg['key']]}
        return mess

    def prepare_commit_follower(self, msg):
        return self.reply_rpc(msg)

    def commit_success(self,msg):
        mess = {"src": self.server.my_id, "dst": msg['src'],
                "leader": self.server.leader, "type": "ok", "MID": msg['MID']}
        self.follower_commit()
        self.prepared_message[self.LogIndex] = mess
        self.num_commits[self.LogIndex] = 1
        self.LogIndex += 1

    def confirm_commit(self):
        mess = {"src": self.server.my_id, "dst": "FFFF",
                "leader": self.server.my_id, "type": "conf"}
        self.follower_commit()
        return mess

    def follower_commit(self):
        self.dict[self.LogTerm[0]] = self.LogTerm[1]
        self.entries.append(self.LogTerm)

    def prepare_keys(self, msg):
        self.prevLogTerm = self.LogTerm
        self.prevLogIndex = self.LogIndex
        self.LogTerm = (msg['key'], msg['value'])

    def index_set(self):
        for replica in range(len(self.server.replica_ids)):
            self.indexes[self.server.replica_ids[replica]] = self.LogIndex

    # plt = the previous index the leader has for the follower
    # pli = the current index of the follower
    def append_entries_rpc(self, server):
        mess = {"src": self.server.my_id, "dst": server,
                "leader": self.server.my_id, "type": "rpc", "term": self.term,
                "plt": self.indexes[server],
                "pli": self.LogIndex,
                "entries": self.entries[self.indexes[server]:],
                "commitIndex": self.leaderCommit}
        return mess

    def send_fail(self, msg):
        mess = {"src": self.server.my_id, "dst": msg['src'],
                "leader": self.server.leader, "type": "fail", "MID": msg['MID']}
        return mess

    def reply_rpc(self, msg):
        self.entries[msg["plt"]:] = msg['entries']
        self.leaderCommit = msg['commitIndex']
        self.LogTerm = msg['plt']
        mess = {"src": self.server.my_id, "dst": msg['leader'],
                "leader": msg['leader'], "type": "prep", "pli": msg['pli']}
        return mess
