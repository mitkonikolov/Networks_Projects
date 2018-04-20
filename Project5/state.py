#!/usr/bin/env python
import time

class State():

    # TODO Clarify committed, applied, replicated
    # a leader broadcasts every 50ms
    BROADCAST_TIMEOUT = 150

    def __init__(self, server):

        # BASIC
        # Persistent State on All Servers
        self.term = 0
        # state can be leader, follower, candidate
        self.state = "follower"
        self.server = server
        # in ms
        self.last_heartbeat = 0

        # ELECTIONS
        # candidate ID
        self.voted_for = None
        # current number of votes for self during elections
        self.vote_count = []

        # MANAGING SYSTEM
        # a list of Entry objects
        self.log = []
        # Volatile State on All Servers
        # new_entry in leader's log -> appended to folowers log -> committed
        # index of highest log entry that was committed (succ stored)
        self.commit_index = -1
        # server -> highest log entry known to be replicated on the server
        self.match_index = {}
        # Volatile State on Leaders
        # server -> index of next log entry to send to that server
        # TODO initialize to current last log entry + 1 => need to know servers
        self.next_index = {}
        # entry -> number of servers who have the entry in their log
        self.entries_count = {}
        # entries that we just found out are ready to be committed (this must
        #  be reset after the commit)
        self.ready_to_commit = []

    def prepare_for_application(self):
        """Generate a message requesting voting.
        :return:
        """
        self.state = "candidate"
        self.term += 1
        self.vote_count.append(self.server.my_id)
        self.voted_for = self.server.my_id
        return {"src": self.voted_for, "dst": "FFFF",
                "leader": self.voted_for, "type": "vote", "term": self.term,
                "log_length": len(self.log)}

    def set_leader(self):
        self.state = "leader"
        # the election is over
        self.__reset_vote_stats()
        self.init_all_next_index()

    def vote(self, msg):
        mess = {"src": self.server.my_id, "dst": msg['leader'],
                "leader": msg['leader'], "type": "vote", "term": msg['term']}
        self.voted_for = msg['leader']
        return mess

    def gen_heartbeat(self, won=False):
        """Generates a heartbeat to announce or maintain leadership.
        :param won: indicates whether this is an announcement of leadership
        :return: a dictionary that represents the heartbeat
        """
        mess = {"src": self.server.my_id, "dst": "FFFF",
                "leader": self.server.my_id, "type": "heart", "term":
                    self.term, "leaderCommit": self.commit_index}
        if won:
            mess["type"] = "won"
        self.last_heartbeat = time.time()*1000
        return mess

    def check_heart(self):
        """Checks whether a heartbea needs to be sent.
        :return: the next heartbeat or None
        """
        if self.state=="leader" and \
                ((time.time()*1000) - self.last_heartbeat) > \
                State.BROADCAST_TIMEOUT:
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
        # self.server.log(" went back to follower")

    def __reset_vote_stats(self):
        self.vote_count = []
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
                    "MID": msg['MID'].encode('utf-8').strip(), "term":self.term}
        elif value=="NA":
            return {"src": self.server.my_id, "dst": msg['src'].encode(
                'utf-8').strip(), "leader": self.server.leader.encode(
                'utf-8').strip(), "type": type,
                    "MID": msg['MID'].encode('utf-8').strip(), "value": "", "term":self.term}
        else:
            return {"src": self.server.my_id, "dst": msg['src'].encode(
                'utf-8').strip(), "leader": self.server.leader.encode(
                'utf-8').strip(), "type": type,
                    "MID": msg['MID'].encode('utf-8').strip(), "value": value, "term":self.term}

    def add_to_log(self, msg):
        """ Adds the msg/entry to the log of leader and sets the
        entries_count for this entry to 1.
        :param msg: entry/msg to be executed
        :return: None
        """
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
        """Initialize next_index for all replicas.
        :return:
        """
        for replica_id in self.server.replica_ids:
            self.next_index[replica_id] = len(self.log)

    def get_append(self, replica_id):
        """Generates append to log message for a specific replica.
        :param replica_id: the id of the replica for which to generate the
        append to log message
        :return: append to log message
        """
        next_replica_indx = self.next_index[replica_id]

        # the replica's log is up-to-date
        if next_replica_indx == len(self.log):
            return False

        # get all entries starting at next index for the replica inclusive
        entries = []
        i = next_replica_indx
        while i < (len(self.log)):
            entries.append(self.log[i])
            i+=1
        if next_replica_indx>0:
            try:
                prevLogTerm = self.log[next_replica_indx-1]['term']
                prevLogIndx = next_replica_indx-1
            except IndexError:
                print "{} error {} {}".format(self.server.my_id, replica_id,
                                            next_replica_indx)
                exit()
        # index is 0
        else:
            entries = self.log
            prevLogTerm = self.term
            # the follower saves the message at prevLogIndx + 1 = 0
            prevLogIndx = -1
        # self.server.log("QWERTY\n\n" + str(entries)+"\n" + str(next_replica_indx) + "\n\n")
        mess = {"src": self.server.my_id, "dst": replica_id, "leader":
            self.server.leader.encode("utf-8").strip(), "type": "append",
                "term": self.term, "prevLogIndx": prevLogIndx,
                "prevLogTerm": prevLogTerm, "entries": entries,
                "leaderCommit": self.commit_index}
        return mess

    def log_consistency(self, msg):
        """Check whether the prevlogindx is in the log and then whether it
        was sent in the same term.
        :param msg: entry to be checked for consistency
        :return: True if the log is consistent
        """
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
        """Add the entries from the msg into the log of the follower self.
        :param msg: message from leader
        :return: None
        """
        append_indx = msg['prevLogIndx'] + 1
        self.log = self.log[:append_indx]

        i = 0
        while i < len(msg['entries']):
            # overwriting data in the log of a follower
            if append_indx < len(self.log):
                self.log[append_indx] = msg['entries'][i]
            else:
                self.log.append(msg['entries'][i])
            self.entries_count[append_indx] = 1
            append_indx += 1
            i += 1

    def gen_append_succ(self, msg):
        """A follower generates a success message after adding to its log.
        :param msg: message containing the info
        :return: dictionary to be sent back as a succ append message
        """
        return {"src": self.server.my_id, "dst": msg['src'],
                "type":"append_succ", "next_index": len(self.log),
                "leader": self.server.leader, "term": self.term}

    def gen_append_reject(self):
        """A follower generates a message for a rejected append message.
        :return: a dictionary representing and append_reject message
        """
        return {"src": self.server.my_id, "dst": self.server.leader,
                "type": "append_reject", "leader": self.server.leader,
                "term": self.term}


    def incr_count_for(self, msg):
        """Updates the next_index for the replica that sent the
        given append_succ msg and increments the entries_counts for the
        appended entries to check whether they are ready for a commit.
        :param msg: append_succ from a follower
        :return: whether there are newly committed messages
        """
        replica_id = msg['src']
        first_entry_ind = self.next_index[replica_id]
        new_next_index = msg['next_index']
        self.next_index[replica_id] = new_next_index
        entry_id = first_entry_ind
        # self.server.log("entry id {} new next indx {} curr commit ind {}"
        #                 .format(entry_id, new_next_index, self.commit_index))
        # go through all the messages that this message says were
        # successfully appended to a follower's log
        while entry_id < new_next_index:
            try:
                self.entries_count[entry_id] += 1
                self.check_ready_for_commit(entry_id)
                entry_id += 1
            except KeyError:
                print("-----------------ERROR---------------")
                print(len(self.entries_count))
                raise RuntimeError
        # self.server.log("comm indx {}".format(self.commit_index))
        return len(self.ready_to_commit) > 0

    def check_ready_for_commit(self, entry_id):
        """Checks whether the entry_id is an entry that becomes newly
        committed and if so adds it to self.ready_to_commit
        :param entry_id: the id of the entry
        :return: None
        """
        if self.entries_count[entry_id] > (len(self.server.replica_ids)/2):
            # self.server.log("so far {} need to be more than {}".format(
            #     self.entries_count[n], (len(self.server.replica_ids)/2)))
            if self.commit_index < entry_id:
                self.commit_index = entry_id
                self.ready_to_commit.append(entry_id)

    def get_new_committed_entries(self):
        """
        :return: self.ready_to_commit
        """
        return self.ready_to_commit

    def gen_new_committed_messages(self):
        """Generate OK messages to be sent to the clients for all successfully
        committed entries.
        :return:
        """
        all_messages = []
        for n in self.ready_to_commit:
            entry = self.log[n]
            all_messages.append(self.gen_mess(entry, "ok"))
        return all_messages

    def reset_ready_to_commit(self):
        self.ready_to_commit = []

    def decr_next_index(self, replica_id):
        """Decrements the next_index for the replica with the given
        replica_id by 1.
        :param replica_id: the id of the replica whose next_index needs to
        be decremented
        :return: True if successful
        """
        self.next_index[replica_id] -= 1
        # check whether the data is uncorrupted
        return self.next_index[replica_id] >= 0

    def update_committed(self, msg):
        """A candidate checks what is the commit_index of the current leader,
        sets its commit index to its highest possible <= the leader's
        commit_index.
        :param msg: message from the leader
        :return:
        """
        leader_commit_index = int(msg['leaderCommit'])
        curr_commit = self.commit_index
        while curr_commit < len(self.log) and curr_commit < leader_commit_index:
            curr_commit += 1
            self.ready_to_commit.append(curr_commit)
        self.commit_index = curr_commit
