#!/usr/bin/env python

import sys, socket, select, time, json, random


class Server:
    # Your ID number
    my_id = sys.argv[1]

    # The ID numbers of all the other replicas
    replica_ids = sys.argv[2:]

    # Connect to the network. All messages to/from other replicas and clients will
    # occur over this socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    sock.connect(my_id)

    leader = "0000"

    last = 0


    def listen(self):
        while True:
            ready = select.select([self.sock], [], [], 0.1)[0]

            if self.sock in ready:
                msg_raw = self.sock.recv(32768)
                self.process_mess(msg_raw)

            clock = time.time()
            if clock - self.last > 2:
                # Send a no-op message to a random peer every two seconds, just for fun
                # You definitely want to remove this from your implementation
                msg = {'src': self.my_id, 'dst': random.choice(
                    self.replica_ids),
                       'leader': 'FFFF', 'type': 'noop'}
                self.sock.send(json.dumps(msg))
                print('%s sending a NOOP to %s' % (msg['src'], msg['dst']))
                last = clock

    def process_mess(self, msg_raw):
        if len(msg_raw) == 0:
            return

        msg = json.loads(msg_raw)

        # For now, ignore get() and put() from clients
        if msg['type'] in ['get', 'put']:
            mess = {"src": self.my_id, "dst": msg["src"], "leader": self.leader,
                    "type": "fail", "MID": msg["MID"]}
            self.sock.send(json.dumps(mess))

        # Handle noop messages. This may be removed from your final implementation
        elif msg['type'] == 'noop':
            print(
                '%s received a NOOP from %s' % (msg['dst'], msg['src']))





