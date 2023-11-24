from socket import *
import sys

"""
if len(sys.argv) <= 1:
   print('Usage : "python proxy.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
   sys.exit(2)
"""
# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
# Fill in start
tcpSerSock.bind(("localhost", 9595))
tcpSerSock.listen(10)
# Fill in end

while 1:
   # Start receiving data from the client
   print('Ready to serve...')
   tcpCliSock, addr = tcpSerSock.accept()
   print('Received a connection from:', addr)

   message = tcpCliSock.recv(4096).decode()

   if not message:
       continue

   print(message)

   # Extract the filename from the given message
   print(message.split()[1])
   filename = message.split()[1].partition("/")[2]
   print(filename)

   fileExist = False

   try:
       # Check whether the file exists in the cache
       f = open(filename, "r", encoding='utf-8')
       fileExist = True
       outputData = f.readlines()

       # ProxyServer finds a cache hit and generates a response message
       tcpCliSock.send("HTTP/1.0 200 OK\r\n".encode())
       tcpCliSock.send("Content-Type:text/html\r\n".encode())

       # Fill in start
       for o in outputData:
           tcpCliSock.send(o.encode())

       # Fill in end

       print('Read from cache')

   # Error handling for file not found in cache
   except IOError:
       if fileExist == False:
           # Create a socket on the proxyserver
           c = socket(AF_INET, SOCK_STREAM)
           hostn = filename.replace("www.", "", 1)

           serverName = filename.partition("/")[0]
           askFile = 'http://' + serverName if ''.join(filename.partition('/')[1:]) == '' else ''.join(filename.partition('/')[1:])

           print(hostn)
           print(serverName, askFile)

           try:
               # Connect to the socket to port 80
               # Fill in start
               c.connect((serverName, 80))
               # Fill in end

               # Create a temporary file on this socket and ask port 80
               # for the file requested by the client
               fileObj = c.makefile('rwb', None)
               h = "GET " + askFile + " HTTP/1.1\r\nHost: " + serverName + '\r\n\r\n'
               fileObj.write(h.encode())

               # Read the response into a buffer
               # Fill in start
               fileObj.flush()

               responseBuffer = fileObj.readlines()

               if responseBuffer[0] == b'404':
                   print('404')
                   tcpCliSock.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
                   tcpCliSock.close()
                   continue

               line = responseBuffer[0].decode()
               code = int(line.split()[1])

               for r in responseBuffer:
                  tcpCliSock.send(r)

               # Fill in end

               # Create a new file in the cache for the requested file
               # Also send the response in the buffer to the client socket
               # and the corresponding file in the cache
               tmpFile = open("./" + filename, "wb")

               # Fill in start
               for r in responseBuffer:
                   tmpFile.write(r)

               tmpFile.close()
               # Fill in end
           except:
               print("Illegal request")
       else:
           # HTTP response message for file not found
           # Fill in start
           tcpCliSock.send("HTTP/1.0 404 NOT FOUND\r\n".encode())
           tcpCliSock.send("Content-Type:text/html\r\n".encode())
           tcpCliSock.send("<html><head><title>Not Found</title></head><body><h1>Not Found</h1></body></html>".encode())
           #Fill in end

   # Close the client and the server sockets
   tcpCliSock.close()
   tcpSerSock.close()