import time
import os
import sys
import socket
import threading
import select

HOST = '127.0.0.1'
PORT = 800
MAX_WAIT_NUM = 5
CONNECTION_TIMEOUT = 120
CONNECTION_INTERVAL = 30
RECV_TIMEOUT = 1
RECV_SIZE = 1024
REQUEST_HEADER_END = '\r\n\r\n'
STATIC_ROOT = os.getcwd()
HOME_PAGE_FILE = 'index.html'
NOT_FOUND_PAGE = '404.html'


def main_http_server(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, int(port)))
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


def parse_request_header(request_header):
    ret_dict = {}
    header_lines = request_header.split('\r\n')
    try:
        ret_dict['request_method'], ret_dict['request_uri'], ret_dict['http_version'] = header_lines[0].split()
        for line in header_lines[1:]:
            if 'Host' in line:
                field_name, field_value = line.split(':', 1)
            else:
                field_name, field_value = line.split(':')
            ret_dict[field_name] = field_value.strip()
    except Exception as e:
        print 'invalid header!!!'
        print e
        print request_header
    return ret_dict


def handle_request(cli_sock, cli_addr):
    # get the http request header.
    cli_sock.settimeout(RECV_TIMEOUT)
    start_time = int(time.time())
    request_content = []
    while int(time.time()) - start_time <= CONNECTION_TIMEOUT:
        if len(request_content) == 0:
            try:
                data = cli_sock.recv(RECV_SIZE)
            except:
                continue
            if data:
                request_content.append(data)
        else:
            if REQUEST_HEADER_END not in request_content[-1]:
                recv_begin_time = int(time.time())
                while int(time.time()) - recv_begin_time <= CONNECTION_INTERVAL:
                    try:
                        data = cli_sock.recv(RECV_SIZE)
                    except:
                        # receive data timeout exception.
                        continue
                    if data:
                        request_content.append(data)
                        break
                    else:
                        break
            else:
                # get the request header completely.
                # get rid of the redundant part after '\r\n\r\n'.
                _index = request_content[-1].index(REQUEST_HEADER_END)
                request_content[-1] = request_content[-1][:_index + 4]
                break

    request_header = ''.join(request_content)
    if len(request_header) > 0 and request_header[-4:] == REQUEST_HEADER_END:
        # parse request header.
        request_header_dict = parse_request_header(request_header[:-4])
        # handle request.
        request_method = request_header_dict.get('request_method', '')
        if request_method == 'GET':
            # TODO: What if the uri includes the escape charactor.
            request_uri = request_header_dict.get('request_uri', '')
            response_body_name = ''
            if request_uri:
                # platform-specific.
                if 'linux' in sys.platform:
                    # now,if the uri = '/hehe.html?user=jyj', we just leave the part after question mark alone.
                    response_body_name = request_uri.split('?')[0]
                else:
                    # default treated as windows system.
                    response_body_name = request_uri.split('?')[0].replace('/', '\\')
                if request_uri == '/':
                    response_body_name = response_body_name + HOME_PAGE_FILE
                else:
                    pass
            else:
                pass
            if response_body_name:
                request_url = '{path_name}{file_name}'.format(path_name=STATIC_ROOT, file_name=response_body_name)
                if os.path.exists(request_url):
                    http_response_code = '200'
                else:
                    http_response_code = '404'
            else:
                http_response_code = '404'
        else:
            # TODO: handle other request methods.
            pass
        # send response.
        if http_response_code == '404':
            if 'linux' in sys.platform:
                path_separator = '/'
            else:
                path_separator = '\\\\'
            request_url = '{path_name}{separator}{file_name}'.format(path_name=STATIC_ROOT, separator=path_separator,
                                                                     file_name=NOT_FOUND_PAGE)
        with open(request_url, 'r') as fp:
            response_body_content = fp.read()
        content_length = len(response_body_content)
        response_desc_dict = {'200': 'OK', '404': 'Not Found'}
        response_header_content = 'HTTP/1.1 {response_code} {response_desc}\r\nServer: jyj_web_server\r\nContent-Type: text/html\r\nContent-Length: {content_length}\r\nConnection: close\r\nVary: Accept-Encoding\r\n\r\n'
        cli_sock.send(response_header_content.format(response_code=http_response_code,
                                                     response_desc=response_desc_dict[http_response_code],
                                                     content_length=content_length))
        cli_sock.send(response_body_content)
    else:
        # invalid request header.
        pass
    cli_sock.close()
    print 'Finished handling the request from %s' % str(cli_addr)

    """
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
    cli_sock.close()
    print 'Finished handling the request from %s' % str(cli_addr)
    """


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main_http_server(sys.argv[1], sys.argv[2])
    else:
        main_http_server()