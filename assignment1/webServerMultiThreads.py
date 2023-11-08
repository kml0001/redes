from socket import *
import threading


def handle_client(connectionSocket, addr):
    try:
        # Recibe el mensaje y verifica el nombre del archivo
        message = connectionSocket.recv(2048).decode()
        filename = message.split()[1]
        f = open(filename[1:], 'r')
        outputdata = f.read()

        print("File found.")
        # Devuelve la línea de encabezado informando que el archivo fue encontrado
        headerLine = "HTTP/1.1 200 OK\r\n"
        connectionSocket.send(headerLine.encode())
        connectionSocket.send("\r\n".encode())

        # Envía el archivo
        for i in range(0, len(outputdata)):
            connectionSocket.send(outputdata[i].encode())
        connectionSocket.send("\r\n".encode())

        # Finaliza la conexión
        print("File sent.")
        connectionSocket.close()

    except IOError:
        print("Warning: file not found.")

        # Devuelve el encabezado de error al navegador
        errHeader = "HTTP/1.1 404 Not Found\r\n"
        connectionSocket.send(errHeader.encode())
        connectionSocket.send("\r\n".encode())

        # Abre y envía la página de error al navegador
        ferr = open("notfound.html", 'r')
        outputerr = ferr.read()

        for i in range(0, len(outputerr)):
            connectionSocket.send(outputerr[i].encode())
        connectionSocket.send("\r\n".encode())

        # Finaliza la conexión
        print("Error message sent.")
        connectionSocket.close()


# Configuración del servidor
serverSocket = socket(AF_INET, SOCK_STREAM)
serverPort = 9595
serverSocket.bind(('', serverPort))
serverSocket.listen(5)
print("Ready to serve . . .")

# Función principal para aceptar solicitudes y crear subprocesos
while True:
    connectionSocket, addr = serverSocket.accept()
    print("Request accepted from (address, port) tuple: %s" % (addr,))

    # Crear un nuevo hilo para manejar la solicitud del cliente
    client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
    client_thread.start()
