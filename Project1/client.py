import socket
import sys
import ssl


class MySocket:
    TCP_IP = '129.10.113.143'
    MAX_BYTES = 256
    mySock = socket
    response = ""
    res = 0

    def connect(self):
        self.mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mySock.connect((self.TCP_IP, 27998))

    def ssl_connect(self):
        self.mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mySock = ssl.wrap_socket(self.mySock)
        self.mySock.connect((self.TCP_IP, 27999))

    def send_init_mess(self):
        self.mySock.send("cs3700spring2018 HELLO 001616080\n")
        self.response = self.mySock.recv(self.MAX_BYTES)

    def check_valid_response(self, words):
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
        try:
            int(num)
            return True
        except ValueError:
            return False

    def perform_operation(self):
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
        self.mySock.send("cs3700spring2018 " + str(s.res) + "\n")
        self.response = self.mySock.recv(self.MAX_BYTES)

    def close(self):
        self.mySock.close()

s = MySocket()
#s.connect()
s.ssl_connect()
s.send_init_mess()
while True:
    s.perform_operation()
    s.send_solution()
