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
        self.commit_index = -1

        # index of highest log entry that was applied to state machine
        self.last_applied = -1

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
        # number of commits for an entry so far
        self.entries_count = {}
        self.committed_changed = []

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
        self.init_all_next_index()


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

    def gen_mess(self, msg, type, value=False):
        """Generates messages to send back to the client.
        :param msg:
        :param type:
        :param value:
        :return:
        """
        if not value:
            return {"src": self.server.my_id, "dst": msg[
                'src'].encode('utf-8').strip(), "leader":
                self.server.leader.encode('utf-8').strip(), "type": type,
                    "MID": msg['MID'].encode('utf-8').strip()}
        else:
            return {"src": self.server.my_id, "dst": msg['src'].encode(
                'utf-8').strip(), "leader": self.server.leader.encode(
                'utf-8').strip(), "type": type,
                    "MID": msg['MID'].encode('utf-8').strip(), "value": value}

    def add_to_log(self, msg):
        src = msg['src']
        mid = msg['MID']
        key = msg['key']
        value = msg['value']
        term = self.term
        # add to log
        self.log.append({"src":src, "MID": mid, "key": key, "value": value,
                         "term": term})
        self.entries_count[len(self.log) - 1] = 1

    def init_all_next_index(self):
        for replica_id in self.server.replica_ids:
            self.next_index[replica_id] = self.__init_indv_next_index()

    def __init_indv_next_index(self):
        curr_len = len(self.log)
        if curr_len==0:
            return 0
        else:
            return curr_len + 1

    def get_append(self, replica_id):
        # if replica_id not in self.next_index:
        #     next_replica_indx = self.__init_indv_next_index()
        #     self.next_index[replica_id] = next_replica_indx
        # else:
        next_replica_indx = self.next_index[replica_id]
        entries = self.log[next_replica_indx:]
        if next_replica_indx>0:
            try:
                prevLogTerm = self.log[next_replica_indx-1]['term']
                prevLogIndx = next_replica_indx-1
            except IndexError:
                print "{} error {} {}".format(self.server.my_id, replica_id,
                                            next_replica_indx)
                exit()
        else:
            prevLogTerm = self.term
            prevLogIndx = -1
        mess = {"src": self.server.my_id, "dst": replica_id, "leader":
            self.server.leader.encode("utf-8").strip(), "type": "append",
                "term": self.term, "prevLogIndx": prevLogIndx,
                "prevLogTerm": prevLogTerm, "entries": entries,
                "leaderCommit": self.commit_index}
        return mess

    def log_consistency(self, msg):
        #This is the first entry to the log
        if len(self.log) == 0:
            return True
        prevLogTerm = msg['prevLogTerm']
        prevLogIndx = msg['prevLogIndx']
        if prevLogIndx < len(self.log):
            log_entry = self.log[prevLogIndx]
            if log_entry['term'] == prevLogTerm:
                return True
        return False

    def append_to_log(self, msg):
        append_indx = msg['prevLogIndx'] + 1
        self.log[append_indx:] = msg['entries']

    def gen_append_succ(self, msg):
        return {"src": self.server.my_id, "dst": msg['src'],
                "type":"append_succ", "next_index": len(self.log),
                "leader": self.server.leader}

    def gen_append_reject(self):
        return {"src": self.server.my_id, "dst": self.server.leader,
                "type": "append_reject", "leader": self.server.leader}

    def incr_count_for(self, msg):
        replica_id = msg['src']
        first_entry_ind = self.next_index[replica_id]
        new_next_index = msg['next_index']
        self.next_index[replica_id] = new_next_index
        self.server.log("prev next_ind {} new next ind {} for replica {}".format(first_entry_ind, new_next_index, replica_id))
        entry_id = first_entry_ind
        while entry_id < new_next_index:
            try:
                self.entries_count[entry_id] += 1
                self.check_ready_for_commit(entry_id)
                entry_id += 1
            except KeyError:
                print("-----------------ERROR---------------")
                print(len(self.entries_count))
                raise RuntimeError
        return len(self.committed_changed) > 0

    def check_ready_for_commit(self, n):
        if self.entries_count[n] > (len(self.server.replica_ids)/2):
            # self.server.log("so far {} need to be more than {}".format(
            #     self.entries_count[n], (len(self.server.replica_ids)/2)))
            print("comm ind {} n {}".format(self.commit_index, n))
            if self.commit_index < n:
                print("-------------------------")
                self.commit_index = n
                self.server.log("comm indx = {}".format(n))
                self.committed_changed.append(n)
            elif self.commit_index == n:
                print "equal"

    def get_new_committed_entries(self):
        return self.committed_changed

    def gen_new_committed_messages(self):
        all_messages = []
        for n in self.committed_changed:
            entry = self.log[n]
            all_messages.append(self.gen_mess(entry, "ok"))
        return all_messages

    def reset_committed_changed(self):
        self.committed_changed = []