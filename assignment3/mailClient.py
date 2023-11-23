from socket import *
import ssl
import base64

msg = "\r\n I love computer networks!" 
endmsg = "\r\n.\r\n"

# Choose a mail server (e.g. Google mail server) and call it mailserver 
mailserver = "smtp.mail.com"
mailserverPort = 587

# Your Gmail credentials
username = 'kmychamo@gmail.com'
password = 'sbbv gcxo kmfn lvjh '

# Create socket called clientSocket and establish a TCP connection with mailserver
#Fill in start
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((mailserver, mailserverPort))
#Fill in end

recv = clientSocket.recv(1024).decode() 
print(recv)
if recv[:3] != '220':
	print('220 reply not received from server.')

# Send HELO command and print server response. 
heloCommand = 'HELO Alice\r\n'
clientSocket.send(heloCommand.encode())
recvHelo = clientSocket.recv(1024).decode() 
print(recvHelo)
if recvHelo[:3] != '250':
	print('250 reply not received from server.')

#-------------------------------------------------------------------------
# Send STARTTLS command and print server response.
starttlsCommand = 'STARTTLS\r\n'
clientSocket.send(starttlsCommand.encode())
recvStarttls = clientSocket.recv(1024).decode()
print(recvStarttls)
if recvStarttls[:3] != '220':
    print('220 reply not received after STARTTLS command.')

# Create an SSL context and wrap the socket with SSL/TLS
context = ssl.create_default_context()
clientSocket = context.wrap_socket(clientSocket, server_hostname=mailserver)

# Send EHLO command again after upgrading to TLS and print server response.
ehloCommand = 'EHLO Alice\r\n'
clientSocket.send(ehloCommand.encode())
recvEhloTls = clientSocket.recv(1024).decode()
print(recvEhloTls)
if recvEhloTls[:3] != '250':
    print('250 reply not received after EHLO command (TLS).')

# Authenticate with the server
authCommand = 'AUTH LOGIN\r\n'
clientSocket.send(authCommand.encode())
recvAuth = clientSocket.recv(1024).decode()
print(recvAuth)
if recvAuth[:3] != '334':
    print('334 reply not received after AUTH LOGIN command.')

# Send the base64-encoded username
clientSocket.send(base64.b64encode(username.encode()) + b'\r\n')
recvUsername = clientSocket.recv(1024).decode()
print(recvUsername)
if recvUsername[:3] != '334':
    print('334 reply not received after sending username.')

# Send the base64-encoded password
clientSocket.send(base64.b64encode(password.encode()) + b'\r\n')
recvPassword = clientSocket.recv(1024).decode()
print(recvPassword)
if recvPassword[:3] != '235':
    print('235 reply not received after sending password. Authentication failed.')

#--------------------------------------------------------------------------

# Send MAIL FROM command and print server response.
#Fill in start
mailFrom = "MAIL FROM: kmychamo@gmail.com\r\n"
clientSocket.send(mailFrom.encode())
recvMail = clientSocket.recv(1024).decode()
print(recvMail)
if recvMail[:3] != '250':
	print('MAIL FROM error : 250 reply not received from server.')
#Fill in end

# Send RCPT TO command and print server response.
# Fill in start
rctpTo = "RCTP TO: nanda.snow.black@gmail.com\r\n"
clientSocket.send(rctpTo.encode())
recvRctp = clientSocket.recv(1024).decode()
print(recvRctp)
if recvRctp[:3] != '250':
    print('RCTP TO error : 250 reply not received from server.')
# Fill in end

# Send DATA command and print server response.
# Fill in start
dataCommand = "DATA:\r\n"
clientSocket.send(dataCommand.encode())
recvData = clientSocket.recv(1024).decode()
print(recvData)
if recvData[:3] != '354':
    print('Data error : 354 reply not received from server.')
# Fill in end

# Send message data.
# Fill in start
clientSocket.send(msg.encode())
# Fill in end

# Message ends with a single period.
# Fill in start
clientSocket.send(endmsg.encode())
recvMsg = clientSocket.recv(1024).decode()
print(recvMsg)
if recvMsg[:3] != '250':
    print('250 reply not received from server.')
# Fill in end

# Send QUIT command and get server response.
# Fill in start
quitCommand = "QUIT: \r\n"
clientSocket.send(quitCommand.encode())
recvQuit = clientSocket.recv(1024).decode()
print(recvQuit)
if recvQuit[:3] != '221':
    print('221 reply not received from server.')

clientSocket.close()
# Fill in end