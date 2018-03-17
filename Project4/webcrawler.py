#!/usr/bin/python -u


import sys
import socket

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("fring.ccs.neu.edu" , 80))

def unchunk():
  read = s.recv(4096)
  index = read.find("Content-Length:") + 16
  index_of_type = read[index:].find("\n") + len(read[:index])
  index_of_data = read.find("<!DOCTYPE")
  length = int(read[index:index_of_type])
  length_currently_read = len(read[index_of_data:]) + 1
  while length_currently_read < length:
    new = s.recv(4096)
    read += new
    length_currently_read += len(new)
  return read



s.sendall("GET /accounts/login/?next=/fakebook HTTP/1.1\nHost: fring.ccs.neu.edu\n\n")
output = unchunk()

cookies = ""
crsf_middle_token = output.find("csrfmiddlewaretoken") + 28
token = output[crsf_middle_token:crsf_middle_token+32]
start = output.find("Set-Cookie:")
posting = "username=" + USERNAME + "&password=" + PASSWORD+"&csrfmiddlewaretoken="+token+"&next=/fakebook/"
while start > 0:
  e = output.find(";",start)
  cookies += "Cookie: " + output[start + 12:e] + "\n"
  start = output.find("Set-Cookie:", start + 1)
s.sendall("POST /accounts/login/ HTTP/1.1\nHost: fring.ccs.neu.edu\nContent-Type: "
+ "application/x-www-form-urlencoded\nContent-Length: " +str(len(posting)) + "\n" + cookies +
"\n\n" + posting)

output = unchunk()
print(output)


blacklist = []
todolist = []


while(todolist):
  print("hi")

s.close()
