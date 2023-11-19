from socket import *

msg = "\r\n I love computer networks!" 
endmsg = "\r\n.\r\n"

# Choose a mail server (e.g. Google mail server) and call it mailserver 
mailserver = "smtp.mail.com"
mailserverPort = 587

# Create socket called clientSocket and establish a TCP connection with mailserver
#Fill in start
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(mailserver, mailserverPort)
#Fill in end

recv = clientSocket.recv(1024).decode() 
print(recv)
if recv[:3] != '220':
	print('220 reply not received from server.')

# Send HELO command and print server response. 
heloCommand = 'HELO Alice\r\n'
clientSocket.send(heloCommand.encode())
recv1 = clientSocket.recv(1024).decode() 
print(recv1)
if recv1[:3] != '250':
	print('250 reply not received from server.')

# Send MAIL FROM command and print server response.
#Fill in start
mailFrom = "MAIL FROM: nanda.snow.black@gmail.com\r\n"
clientSocket.send(mailFrom.encode())
recv2 = clientSocket.recv(1024).decode()
print(recv2)
if recv2[:3] != '250':
	print('MAIL FROM error : 250 reply not received from server.')
#Fill in end

# Send RCPT TO command and print server response.
# Fill in start
rctpTo = "RCTP TO: kmychamo@gmail.com\r\n"
clientSocket.send(rctpTo.encode())
recv3 = clientSocket.recv(1024).decode()
print(recv3)
if recv3[:3] != '250':
    print('RCTP TO error : 250 reply not received from server.')
# Fill in end

# Send DATA command and print server response.
# Fill in start
dataCommand = "DATA: asd\r\n"
clientSocket.send(dataCommand.encode())
recv4 = clientSocket.recv(1024).decode()
print(recv4)
if recv4[:3] != '250':
    print('Data error : 250 reply not received from server.')
# Fill in end

# Send message data.
# Fill in start
clientSocket.send('\r\n')
for m in msg:
    clientSocket.send(m)
# Fill in end

# Message ends with a single period.
# Fill in start
clientSocket.send(endmsg)
# Fill in end

# Send QUIT command and get server response.
# Fill in start
quitCommand = "QUIT: \r\n"
clientSocket.send(quitCommand.encode())
recv5 = clientSocket.recv(1024).decode()
print(recv5)
# Fill in end