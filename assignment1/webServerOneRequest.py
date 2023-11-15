#import socket module
from socket import *
import sys # In order to terminate the program

#Prepare a sever socket

#Fill in start
serverSocket = socket(AF_INET, SOCK_STREAM)

# Arbitrary port number
serverPort = 9595 

# Binding the port to the socket
serverSocket.bind(('',serverPort)) 

# Waiting for a request
serverSocket.listen(1) 
#Fill in end

while True:
    #Establish the connection
    print('Ready to serve...')
    
    # Accepting request
    #Fill in start
    connectionSocket, addr = serverSocket.accept() 
    print("Request accepted from (address, port) tuple: %s" % (addr,))
    #Fill in end 

    try:
        # Recieve message and check file name
        
        #Fill in start
        message = connectionSocket.recv(2048).decode()
        #Fill in end 
        
        filename = message.split()[1]
        f = open(filename[1:], 'r')
        
        #Fill in start
        outputdata = f.read()
        #Fill in end 

        print("File found.")
        
        #Send one HTTP header line into socket
        
        #Fill in start
        # Returns header line informing that the file was found
        headerLine = "HTTP/1.1 200 OK\r\n"
        connectionSocket.send(headerLine.encode())
        connectionSocket.send("\r\n".encode())
        #Fill in end 

        #Send the content of the requested file to the client
        for i in range(0, len(outputdata)):
            connectionSocket.send(outputdata[i].encode())
        connectionSocket.send("\r\n".encode())

        # Terminates the conection
        print("File sent.")
        connectionSocket.close()

    except IOError:
        #Send response message for file not found
        
        #Fill in start 
        print("Warning: file not found.")

        # Returns the error header to the browser
        errHeader = "HTTP/1.1 404 Not Found\r\n"
        connectionSocket.send(errHeader.encode())
        connectionSocket.send("\r\n".encode())

        # Opens and sends the error page to the browser
        ferr = open("notfound.html", 'r')
        outputerr = ferr.read()

        for i in range(0, len(outputerr)):
            connectionSocket.send(outputerr[i].encode())
        connectionSocket.send("\r\n".encode())
        #Fill in end

        #Close client socket
        #Fill in start
        print("Error message sent.")
        connectionSocket.close()
        #Fill in end 

    # Closes the application
    serverSocket.close()
    sys.exit() #Terminate the program after sending the corresponding data 
