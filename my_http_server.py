import sys
import socket
import threading

HOST = '127.0.0.1'
PORT = 800
MAX_WAIT_NUM = 5

def main_http_server(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(MAX_WAIT_NUM)
    print 'Start my http server!'
    while True:
        try:
            print 'Waiting for connection...'
            cli_sock, cli_addr = s.accept()
            print 'the client:%s connect to my http server!' % str(cli_addr)
            t = threading.Thread(target=handle_request, args=(cli_sock, cli_addr))
        except KeyboardInterrupt:
            break
    print 'Stop my http server!'
        
def handle_request(cli_sock, cli_addr):
    with open('E:\\my_http_request.txt', 'w') as fp:
        while True:
            data = cli_sock.recv(1024)
            if data:
                #print data
                fp.write(data)
            else:
                break
        cli_sock.send('Successful!')
        cli_sock.close()
    print 'Finished handling the request from %s' % cli_addr
        
if __name__ == '__main__':
    if len(sys.argv) == 3:
        main_http_server(sys.argv[1], sys.argv[2])
    else:
        main_http_server()