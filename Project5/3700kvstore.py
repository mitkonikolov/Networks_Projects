#!/usr/bin/env python

import sys, socket, select, time, json, random
from state import State

class Server:



    def __init__(self):
        # Your ID number
        self.my_id = sys.argv[1]

        # The ID numbers of all the other replicas
        self.replica_ids = sys.argv[2:]

        # Connect to the network. All messages to/from other replicas and clients will
        # occur over this socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.sock.connect(self.my_id)

        self.leader = "FFFF"
        self.state = State(self)
        self.reset_timeout()
        self.reset_last()

        # the data stored on this server
        self.data = {}

        # last time a leader heard from a replica
        self.replica_time = {}


    def get_timeout(self):
        return self.timeout

    def reset_timeout(self):
        self.timeout = int((random.random() * 150) + 450)

    def reset_last(self):
        """Sets the last time a heartbeat has been sent to the current time
        in miliseconds.
        :return: None
        """
        self.last = time.time() * 1000

    def get_state(self):
        return self.state.state

    def create_rpc(self, dst, type):
        # Send a no-op message to a random peer every two seconds, just for fun
        # You definitely want to remove this from your implementation
        return {"src": self.my_id, "dst": dst, "leader": self.leader, "type": type}

    def listen(self):
        self.reset_last()
        while True:
            ready = select.select([self.sock], [], [], 0.1)[0]
            # check whether a heartbeat needs to be sent
            mess = self.state.check_heart()
            # heartbeat does indeed need to be sent
            if mess is not None:
                self.send(mess)

            if self.state.is_leader(): self.commit()

            if self.sock in ready:
                msg_raw = self.sock.recv(32768)

                if len(msg_raw) == 0: continue

                self.process_mess(msg_raw)

            clock = time.time() * 1000.0
            if self.state.state != "leader" and clock - self.last > \
                    self.timeout:
                # self.log("{} and timeout is  {}".format((clock - self.last),
                #                                    self.timeout))
                # self.log("timedout, became candidate  " + self.my_id)
                self.become_candidate()

            # ready = select.select([self.sock], [], [], 0.1)[0]
            #
            # if self.sock in ready:
            #     msg_raw = self.sock.recv(32768)
            #     print("{} received a mess from {}".format(msg['dst'], msg['src']))
                #self.process_mess(msg_raw)
            # clock = time.time() *1000.0
            # if self.state.state == "follower" and clock - self.last > self.timeout:
            #     print("timedout, became candidate  " + self.my_id)
            #     self.become_candidate()

    def become_candidate(self):
        """Generates message requesting vote, sets current state to candidate
        and votes for itself
        :return: None
        """
        self.log(" became a candidate")
        self.reset_timeout()
        msg = self.state.prepare_for_application()
        self.send(msg)
        # reset the timer
        self.reset_last()

    def send(self, msg):
        # if "MID" in msg:
        #     self.log(msg)
        self.sock.send(json.dumps(msg))

    def process_mess(self, msg_raw):
        if len(msg_raw) == 0:
            return

        # print(self.log("received mess {}".format(msg_raw)))
        msg = json.loads(msg_raw)
        msg_type = msg['type']
        # the message is from self, not for self, or from an old term
        if msg['src'] == self.my_id or \
                (msg['dst'] != self.my_id and msg['dst'] != 'FFFF'):
            return
        self.log(msg)


        if ('term' in msg and
                msg['term'] > self.state.term):
            self.state.term = msg['term']
            self.state.go_back_to_follower()

        # forward on to the leader
        # if msg['type'] in ['get', 'put']:
        #     mess = {"src": self.my_id, "dst": msg["src"], "leader": self.leader,
        #             "type": "fail", "MID": msg["MID"]}
        #     self.sock.send(json.dumps(mess))

        # the current term already has a candidate
        if msg_type == 'heart' and msg['term'] == self.state.term:
            if self.state.is_candidate():
                self.state.go_back_to_follower()
                if msg['leader'] != "FFFF":
                    self.leader = msg['leader']
            self.reset_last()
        # the election was won so self needs to update its leader
        elif msg_type == 'won' and msg['term'] == self.state.term:
            if msg['leader'] != "FFFF":
                self.leader = msg['leader']
            # self.log("election was won updating leader to {}"
    #         .format(self.leader))
            self.state.go_back_to_follower()
            self.reset_last()
        elif msg_type == 'vote' and not self.state.is_leader() and msg['term'] == self.state.term:
            # self is a candidate and is getting a vote
            if self.state.is_candidate() and msg['leader'] == self.my_id:
                if msg['src'] not in self.state.voted_for:
                    self.state.voted_for.append(msg['src'])
                self.log(" received vote from {} now have {} votes".format(
                    msg['src'], self.state.vote_count))
                # self.log("there are {} replicas".format(len(self.replica_ids)))
                if len(self.state.vote_count) > (len(self.replica_ids)/2):
                    self.become_leader()
                    # self.log("won election and became leader")
                # current time in ms
                self.replica_time[msg['src']] = time.time() * 1000
                self.reset_last()
            # self is not a candidate and it has not voted
            elif ((self.state.voted_for is None or
                  self.state.voted_for == msg['src']) and self.state.is_follower()
                  and msg['term'] == self.state.term):
                if 'log_length' in msg and \
                        msg['log_length'] >= len(self.state.log):
                    self.log(" vote for {} sending {}".format(msg['src'],
                                                              self.state.vote(msg)))
                    self.send(self.state.vote(msg))
                self.state.term = msg['term']
                # else:
                #     self.log("didn't vote for {} cand's term {} log len"
                #              " {}".format(msg['src'], msg['term'],
                #                           msg['log_length']))
                self.reset_last()
        elif msg_type == 'get':
            if self.state.is_leader():
                key = msg['key']
                if key in self.data:
                    value = self.data[key]
                    self.send(self.state.gen_mess(msg, "ok", value))
                else:
                    # TODO confirm that this is indeed an OK mess
                    self.send(self.state.gen_mess(msg, "ok", "NA"))
            # no established leader
            elif self.state.is_candidate():
                self.send(self.state.gen_mess(msg, "fail"))
            elif self.state.is_follower():
                # we do not know the leader
                if self.leader == "FFFF":
                    self.send(self.state.gen_mess(msg, "fail"))
                else:
                    self.send(self.state.gen_mess(msg, "redirect"))
        elif msg_type == "put":
            if self.state.is_leader():
                self.state.add_to_log(msg)
                self.commit()
            elif self.state.is_candidate():
                self.send(self.state.gen_mess(msg, 'fail'))
            elif self.state.is_follower():
                if self.leader == "FFFF":
                    self.send(self.state.gen_mess(msg, 'fail'))
                else:
                    self.send(self.state.gen_mess(msg, "redirect"))
        elif msg_type == "append":

            if msg['term'] < self.state.term:
                self.send(self.state.gen_append_reject())
                return

            if self.state.is_candidate():
                self.state.go_back_to_follower()
                if msg['leader'] != 'FFFF':
                    self.leader = msg['leader']
                else:
                    return


            # checks if the prevLogIndx/Term is correctly in log
            if self.state.log_consistency(msg):
                self.state.append_to_log(msg)
                self.state.update_committed(msg)
                self.update_data(self.state.get_new_committed_entries())
                self.state.reset_ready_to_commit()
                append_succ = self.state.gen_append_succ(msg)
                self.send(append_succ)
            else:
                self.send(self.state.gen_append_reject())
            self.reset_last()
        elif msg_type == "append_succ" and self.state.is_leader() and msg['term'] == self.state.term:
            # check whether the message can be committed
            if self.state.incr_count_for(msg):
                updated_entries = self.state.get_new_committed_entries()
                self.update_data(updated_entries)
                all_messages = self.state.gen_new_committed_messages()
                for m in all_messages:
                    self.send(m)
                self.state.reset_ready_to_commit()
            # current time in ms
            self.replica_time[msg['src']] = time.time() * 1000
        elif msg_type == "append_reject" and self.state.is_leader() and msg['term'] == self.state.term:
            if self.state.decr_next_index(msg['src']):
                # current time in ms
                self.replica_time[msg['src']] = time.time() * 1000
            else:
                raise RuntimeError("Incorrect next_index for replica")

    def update_data(self, updated_entries):
        """Performs the change requested by the entry.
        :param updated_entries: a set of entries to be performed
        :return: None
        """
        for entry_id in updated_entries:
            entry = self.state.log[entry_id]
            try:
                self.data[entry['key']] = entry['value']
            except TypeError:
                print("Entry is {}".format(entry))
                exit()


    def commit(self):
        """Sends an append to log message to all followers.
        :return: None
        """
        for replica_id in self.replica_ids:
            curr_time = time.time() * 1000
            if (curr_time - self.replica_time[replica_id]) > 3000:
                append_msg = self.state.get_append(replica_id)
                if append_msg:
                    self.send(append_msg)
            # else:
            #     append_msg = {"src": self.my_id, "dst": replica_id,
            #                          "leader": self.leader.encode(
            #                              "utf-8").strip(), "type": "append",
            #     "term": -1, "prevLogIndx": -1,
            #     "prevLogTerm": -1, "entries": [],
            #     "leaderCommit": self.state.commit_index}



    def become_leader(self):
        """Set all values for leadership.
        :return: None
        """
        self.leader = self.my_id
        self.state.set_leader()
        self.send(self.state.gen_heartbeat(True))
        self.log(" became a leader")
        for replica_id in self.replica_ids:
            self.replica_time[replica_id] = (time.time()*1000)

    def log(self, mess, error=False):
        if error:
            print("[err] {}".format(mess))
        else:
            # print("[mess] {} {} {}".format(time.time(), self.my_id, mess))
            assert(1==1)

    def my_type(self, msg_type):
        return msg_type == 'heart' or msg_type == 'won' or msg_type == \
               'vote' or msg_type == 'append'




if __name__ =="__main__":
    s = Server()
    s.listen()

    # TODO
    #   TODO Elections
    #           +DONE add checking log length before voting
    #   +DONE Add an append failure if the prevlogindex is different from what
    #           we have in the log as a follower

    # TODO Add info about committed messages into heartbeats as well and have
    #  the followers utilize it