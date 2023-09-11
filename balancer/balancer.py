import socket
import os
import sys
import datetime
import signal
import time
from datetime import datetime
import random


BUFFER_SIZE = 1024
TIME = 120
FORMAT = '%H:%M:%S' #format wanted

# Signal handler for graceful exiting.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    sys.exit(0)

def prepare_get_message(host, port, file_name):
    request = f'GET {file_name} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n' 
    return request

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# Read a file from the socket and save it out.

def save_file_from_socket(sock, bytes_to_read, file_name):

    with open(file_name, 'wb') as file_to_write:
        bytes_read = 0
        while (bytes_read < bytes_to_read):
            chunk = sock.recv(BUFFER_SIZE)
            bytes_read += len(chunk)
            file_to_write.write(chunk)

def prepare_response_message(value, host, port, filename):
    date = datetime.now()
    date_string = 'Date: ' + date.strftime('%a, %d %b %Y %H:%M:%S EDT')
    message = 'HTTP/1.1 '
    if value == '301':
        message = message + value + ' Moved Permanently\r\n' + 'Location: http://'+host+':'+port+'/'+filename+ '\r\n' + date_string + '\r\n'
    return message

def send_response_to_client(sock, code, fname, host, port, filename):

    type = 'text/html'
    
    
    # Get size of file

    file_size = os.path.getsize(fname)

    # Construct header and send it

    header = prepare_response_message(code, host, port, filename) + 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size)  + '\r\n\r\n'
    
    sock.send(header.encode())

    # Open the file, read it, and send it

    with open(fname, 'rb') as file_to_send:
        while True:
            chunk = file_to_send.read(BUFFER_SIZE)
            if chunk:
                sock.send(chunk)
            else:
                break

def main():

    # Check command line arguments to retrieve a URL.

    numargs = len(sys.argv)
    print (numargs)
    print(sys.argv)

    saveargs = [''] * (numargs-1)

    times = [''] * (numargs-1)

    hosts = [''] * (numargs-1)
    ports = [''] * (numargs-1)

    weights = [''] * (numargs-1)
    
    total = 0

    for x in range (0, numargs-1):
        saveargs[x] = sys.argv[x+1]
        weights[x] = x+1
        total = total + weights[x]
        

    

    



    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    balancer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    balancer_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(balancer_socket.getsockname()[1]))
    balancer_socket.listen(1)

    while(1):

        for x in range (0, len(saveargs)):
            print('connecting to server' + str(x) + ' ...')
            try:
                savenum = saveargs[x].split(':')
                bsocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                hosts[x] = savenum[0]
                ports[x] = savenum[1]
                bsocket. connect ((savenum[0], int(savenum[1])))

                msg = prepare_get_message(hosts[x], ports[x], 'test.txt')

                curr = datetime.now() # get time before
                bsocket.send(msg.encode())
                response_line = get_line_from_socket(bsocket)
                response_list = response_line.split(' ')
                headers_done = False
                bytes_to_read = 0
                while (not headers_done):
                    header_line = get_line_from_socket(bsocket)
                    header_list = header_line.split()
                    if (header_line == ''):
                        headers_done = True
                    elif (header_list[0] == 'Content-Length:'):
                        bytes_to_read = int(header_list[1])
                save_file_from_socket(bsocket, bytes_to_read, 'test1.txt')
                after = datetime.now() # get time after

                curr = curr.strftime(FORMAT)
                after = after.strftime(FORMAT)
                tdelta = datetime.strptime(curr, FORMAT) - datetime.strptime(after, FORMAT) # find the difference of time in seconds and make an int
                totalt = int(tdelta.total_seconds())

                times[x] = totalt

            except ConnectionRefusedError:
                print('Error:  server '+str(x)+' is not accepting connections.')
                sys.exit(1)


        zippedlists = zip(times, hosts, ports)
        
        sortedpairs = sorted(zippedlists)

        weightedlist = []

        for x in range (0, len(saveargs)):
            print(sortedpairs[x])
            print(weights[x])
            weightedlist = weightedlist + [sortedpairs[x]] * weights[x]

        tuples = zip(*sortedpairs)
        times, hosts, ports = [ list(tuple) for tuple in  tuples]

        print(weightedlist)

        pickaserver = random.randint(1, total)

        print (pickaserver)

        chosen = weightedlist[pickaserver-1]

        timechosen = chosen[0]
        hostchosen = chosen[1]
        portchosen = chosen[2]

        print(timechosen)
        print(hostchosen)
        print(portchosen)

        print('Will wait for client connections at port ' + str(balancer_socket.getsockname()[1]))


        print('Waiting for incoming client connection ...')
        conn, addr = balancer_socket.accept()
        print('Accepted connection from client address:', addr)
        print('Connection to client established, waiting to receive message...')

        # We obtain our request from the socket.  We look at the request and
        # figure out what to do based on the contents of things.

        request = get_line_from_socket(conn)
        print('Received request:  ' + request)

        request_list = request.split()

        req_file = request_list[1]
        while (req_file[0] == '/'):
            req_file = req_file[1:]

        print('Sending 301 to client at: '+hostchosen+':'+portchosen)
        send_response_to_client(conn, '301', '301.html', hostchosen, portchosen, req_file)

        
    
    balancer_socket.close();

        


        





if __name__ == '__main__':
    main()