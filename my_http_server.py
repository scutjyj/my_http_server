import time
import os
import sys
import socket
import threading
import select

HOST = '127.0.0.1'
PORT = 800
MAX_WAIT_NUM = 5

def main_http_server(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(MAX_WAIT_NUM)
    print 'Start my http server!'
    read_list = [s]
    while True:
        try:
            print 'Waiting for connection...'
            readable, writable, errored = select.select(read_list, [], [], 1)
            for _s in readable:
                # notice: the calling of accept() is blocking type.So use select module to implement the asynchronous programming.
                cli_sock, cli_addr = _s.accept()
                print 'the client:%s connect to my http server!' % str(cli_addr)
                t = threading.Thread(target=handle_request, args=(cli_sock, cli_addr))
                t.start()
        except KeyboardInterrupt:
            break
    print 'Stop my http server!'
    t.join()
    s.close()
    
def handle_request(cli_sock, cli_addr):
    # get the http request header.
    cli_sock.settimeout(1)
    with open('E:\\my_http_request_{sock}.txt'.format(sock=cli_addr[1]), 'w') as fp:
        while True:
            print 'before recving...'
            try:
                data = cli_sock.recv(1024)
            except:
                data = None
            print data
            print 'after recving...'
            #time.sleep(1)
            if data:
                #print data
                fp.write(data)
                
            else:
                break
    # send the http response header.
    cli_sock.send('HTTP/1.1 200 OK\r\nServer: nginx\r\nDate: Fri, 30 Mar 2018 13:32:39 GMT\r\nContent-Type: text/html\r\nContent-Length: 52\r\nConnection: close\r\nLast-Modified: Fri, 30 Mar 2018 13:30:57 GMT\r\nVary: Accept-Encoding\r\nExpires: Fri, 30 Mar 2018 13:33:09 GMT\r\nCache-Control: max-age=60\r\n\r\n')
    # send the http response content.
    cli_sock.send('<html><head></head><body>Hello, world!</body></html>')
    #cli_sock.send('Successful!')
    cli_sock.close()
    print 'Finished handling the request from %s' % str(cli_addr)
        
if __name__ == '__main__':
    if len(sys.argv) == 3:
        main_http_server(sys.argv[1], sys.argv[2])
    else:
        main_http_server()