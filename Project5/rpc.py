#!/usr/bin/env python

class Rpc:

    def __init__(self, term, leader_cand_id, prev_last_ind, prev_last_term,
                                           type, entries=None):
        self.term = term

        #self.leader_cand_id = leader_cand_id

        # prev if a leader and last if a candidate
        # self.prev_last_ind = 0
        # self.prev_last_term = 0

        # "append", "vote", "heart", "put", "get"
        self.type = type

        # Append RPC
        # a list of Entry objects unless vote/heart when it's empty
        if entries is None:
            self.entries = []
        else:
            self.entries = entries


