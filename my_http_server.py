# encoding: utf-8

import time
import os
import sys
import socket
import threading
import select
import urllib
import logging

HOST = '127.0.0.1'
PORT = 800
MAX_WAIT_NUM = 5
CONNECTION_TIMEOUT = 120
CONNECTION_INTERVAL = 30
RECV_TIMEOUT = 1
RECV_SIZE = 1024
SEND_SIZE = 1024
REQUEST_HEADER_END = '\r\n\r\n'
STATIC_ROOT = os.getcwd()
LOG_FILE_NAME = 'my_http_server.log'
LOG_PATH = os.path.join(STATIC_ROOT, LOG_FILE_NAME)
SERVER_NAME = 'my_http_server'
HOME_PAGE_FILE = 'index.html'
NOT_FOUND_PAGE = '404.html'

# the STOP_SIGN is a mutable variable used for synchrozing the multi threads.
# notes: the  STOP_SIGN must be mutable,i.e, it can not be string.
STOP_SIGN = []

# set the logger.
logger = logging.getLogger(SERVER_NAME)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
file_handler = logging.FileHandler(LOG_PATH)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.formatter = formatter
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)


def main_http_server(host=HOST, port=PORT, *args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((host, int(port)))
    except:
        logger.error('Please check the host and port!!!Make sure the port is not occupied!!!')
    s.listen(MAX_WAIT_NUM)
    logger.debug('Start my http server!')
    read_list = [s]
    thread_list = []
    while True:
        try:
            #logger.debug('Waiting for connection...')
            readable, writable, errored = select.select(read_list, [], [], 1)
            for _s in readable:
                # notice: the calling of accept() is blocking type.So use select module to implement the asynchronous programming.
                cli_sock, cli_addr = _s.accept()
                logger.debug('the client:%s connect to my http server!' % str(cli_addr))
                # TODO: Use thread.Event to solve the second problem in development_note.txt.
                t = threading.Thread(target=handle_request, args=(cli_sock, cli_addr))
                t.setName(cli_addr[0] + ':' + str(cli_addr[1]))
                thread_list.append(t)
                t.start()
        except KeyboardInterrupt:
            logger.debug('Stop my http server!')
            # close the serving sock.
            s.close()
            STOP_SIGN.append('stop')
            for t in thread_list:
                thread_name = t.getName()
                logger.debug('stopping the thread[%s]...' % thread_name)
                t.join()
                logger.debug('the thread[%s] has been stopped!' % thread_name)
            break


def parse_request_header(request_header):
    ret_dict = {}
    header_lines = request_header.split('\r\n')
    try:
        ret_dict['request_method'], ret_dict['request_uri'], ret_dict['http_version'] = header_lines[0].split()
        for line in header_lines[1:]:
            field_name, field_value = line.split(':', 1)
            ret_dict[field_name] = field_value.strip()
    except Exception as e:
        logger.error('invalid header!!!')
        logger.error('the request header is:%s' % request_header)
        #print e
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
        logger.debug('request header:\n%s' % request_header_dict)
        # handle request.In fact, this is what application program should do.
        request_method = request_header_dict.get('request_method', '')
        if request_method == 'GET':
            _request_uri = request_header_dict.get('request_uri', '')
            # handle escape charactor.
            request_uri = urllib.unquote(_request_uri)
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
                print request_url
                if os.path.exists(request_url):
                    if not os.path.isdir(request_url):
                        http_response_code = '200'
                    else:
                        http_response_code = '404'
                else:
                    http_response_code = '301'
            else:
                http_response_code = '404'
        else:
            # TODO: handle other request methods.
            pass

        # send response.
        # If it is a general web application framework, the code below can be encapsulated as API.
        response_desc_dict = {'200': 'OK', '301': 'Moved Permanently', '404': 'Not Found'}
        # content type refers to the MIME standard.
        content_type_dict = {'mp3': 'audio/mpeg', 'pdf': 'application/pdf', 'jpg': 'image/jpeg', 'css': 'text/css',
                             'mp4': 'video/mp4'}
        if http_response_code == '404':
            if 'linux' in sys.platform:
                path_separator = '/'
            else:
                path_separator = '\\\\'
            request_url = '{path_name}{separator}{file_name}'.format(path_name=STATIC_ROOT, separator=path_separator,
                                                                     file_name=NOT_FOUND_PAGE)

        if http_response_code == '301':
            response_header_content = 'HTTP/1.1 {response_code} {response_desc}\r\nServer: jyj_web_server\r\nConnection: close\r\nVary: Accept-Encoding\r\nLocation: {redirect_url}\r\n\r\n'
            cli_sock.send(response_header_content.format(response_code=http_response_code,
                                                         response_desc=response_desc_dict[http_response_code],
                                                         redirect_url='http://www.baidu.com'))
        else:
            with open(request_url, 'rb') as fp:
                response_body_content = fp.read()
            content_length = len(response_body_content)
            # find out the Content-Type.
            _request_url = request_url.split('.')
            if len(_request_url) == 2:
                url_suffix = _request_url[1]
            else:
                url_suffix = ''
            content_type = content_type_dict.get(url_suffix, 'text/html')
            response_header_content = 'HTTP/1.1 {response_code} {response_desc}\r\nServer: jyj_web_server\r\nContent-Type: {content_type}\r\nContent-Length: {content_length}\r\nConnection: close\r\nVary: Accept-Encoding\r\n\r\n'
            cli_sock.send(response_header_content.format(response_code=http_response_code, content_type=content_type,
                                                         response_desc=response_desc_dict[http_response_code],
                                                         content_length=content_length))

            # To stop the thread blocked by sending a huge file as soon as possible, send the file in piece.
            tmp_pos = 0
            while response_body_content[tmp_pos:tmp_pos+SEND_SIZE]:
                if not STOP_SIGN:
                    try:
                        cli_sock.send(response_body_content[tmp_pos:tmp_pos+SEND_SIZE])
                    except socket.timeout:
                        # In case the peer tcp window is full.
                        continue
                    except socket.error:
                        # the another peer close the socket.
                        break
                    tmp_pos += SEND_SIZE
                    if tmp_pos > content_length:
                        break
                else:
                    break

    else:
        # invalid request header.
        pass
    cli_sock.close()
    logger.debug('Finished handling the request from %s' % str(cli_addr))


if __name__ == '__main__':
    """
    if len(sys.argv) == 3:
        main_http_server(sys.argv[1], sys.argv[2])
    else:
        main_http_server()
    """
    main_http_server(*sys.argv[1:])
