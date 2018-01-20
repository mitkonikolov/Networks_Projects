import socket
import sys
import ssl
import argparse


class MySocket:
    TCP_IP = ''
    STUDENT_ID = ''
    PORT_NUM = 0
    MAX_BYTES = 256
    mySock = socket
    response = ""
    res = 0

    def connect_with(self, args):
        """Uses the data provided in args to connect correctly"""
        self.TCP_IP = args.hostname[0]
        self.STUDENT_ID = args.id[0]
        if args.p is None:
            self.PORT_NUM = 27998
        else:
            self.PORT_NUM = args.p[0]
        self.mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # ssl connection so it needs to be wrapped
        if args.s == True:
            self.mySock = ssl.wrap_socket(self.mySock)
        self.mySock.connect((self.TCP_IP, self.PORT_NUM))

    def send_init_mess(self):
        """Sends the initial message to the host."""
        self.mySock.send("cs3700spring2018 HELLO " + self.STUDENT_ID + "\n")
        self.response = self.mySock.recv(self.MAX_BYTES)

    def check_valid_response(self, words):
        """Returns True if the response is valid.
        
        If the response is invalid or is the final message "BYE ...", then it
        terminates.
        """
        # check list's length and first word
        if (len(words)==3 or len(words)==5) and words[0] == "cs3700spring2018":
            if words[1] == "STATUS":
                # numbers are ints and second number is followed by \n
                if self.is_int_num(words[2]) and self.is_int_num(words[4]) \
                        and words[4][-1:]=="\n":
                    if words[3]=="+" or words[3]=="-" or words[3]=="*" or \
                                    words[3]=="/":
                        return True
            elif words[2] == "BYE\n" and words[1] != "":
                print(words[1])
                self.close()
                sys.exit(0)
        sys.stderr("The response by the server is invalid")
        sys.exit(1)

    @staticmethod
    def is_int_num(num):
        """Returns a bool indicating if num is an int in the correct range."""
        try:
            n = int(num)
            if 1 <= n <= 1000:
                return True
            return False
        except ValueError:
            return False

    def perform_operation(self):
        """Solve the problem that the host has sent."""
        words = self.response.split(" ")
        self.check_valid_response(words)
        oper = words[3]
        num1 = int(words[2])
        num2 = int(words[4])
        if oper=="+":
            self.res = num1+num2
        elif oper=="-":
            self.res = num1-num2
        elif oper=="*":
            self.res = num1*num2
        else:
            self.res = num1/num2

    def send_solution(self):
        """Send the solution to the problem."""
        self.mySock.send("cs3700spring2018 " + str(s.res) + "\n")
        self.response = self.mySock.recv(self.MAX_BYTES)

    def close(self):
        """Close the connection with the host."""
        self.mySock.close()

parser = argparse.ArgumentParser()
parser.add_argument('-p', nargs=1, type=int, help='port number', metavar='port')
parser.add_argument('-s', default=False, help='indicates SSL connection',
                    action="store_true")
parser.add_argument('hostname', nargs=1, type=str, help='the '
                    'name or address of the host', metavar='hostname')
parser.add_argument('id', nargs=1, type=str, help='student ID', metavar='NEU '
                                                                        'ID')
args = parser.parse_args()
s = MySocket()
s.connect_with(args)
s.send_init_mess()
while True:
    s.perform_operation()
    s.send_solution()