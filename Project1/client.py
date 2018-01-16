import socket


class MySocket:
    TCP_IP = '129.10.113.143'
    MAX_BYTES = 256
    mySock = socket
    response = ""

    def connect(self):
        self.mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mySock.connect((self.TCP_IP, 27998))

    def send_init_mess(self):
        self.mySock.send("cs3700spring2018 HELLO 001616080\n")
        self.response = self.mySock.recv(self.MAX_BYTES)

    def check_valid_response(self):
        words = self.response.split(" ")
        # check whether the response was valid and if it was
        print(self.perform_operation(int(words[2]), words[3], int(words[4])))

    @staticmethod
    def perform_operation(num1, oper, num2):
        if oper=="+":
            return num1+num2
        elif oper=="-":
            return num1-num2
        elif oper=="*":
            return num1*num2
        else:
            return num1/num2

    def print_response(self):
        self.mySock.close()
        print(self.response)

s = MySocket()
s.connect()
s.send_init_mess()
s.print_response()
s.check_valid_response()
