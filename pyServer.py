import socket
import select
import time
from threading import Thread
import json
import colorama

class bcolors:
    reset = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

    black = '\033[90m'
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'    
    blue = '\033[94m'
    purple = '\033[95m'
    cyan = '\033[96m'
    white = '\033[97m'

class SocketServer(Thread):
    def __init__(self, host = '0.0.0.0', port = 3334, max_clients = 3):
        """ Initialize the server with a host and port to listen to.
        Provide a list of functions that will be used when receiving specific data """
        Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.sock.bind((host, port))
        self.sock.listen(max_clients)
        self.sock_threads = []
        self.counter = 0 # Will be used to give a number to each thread

    def close(self):
        """ Close the client socket threads and server socket if they exists. """
        print('Closing server socket (host {}, port {})'.format(self.host, self.port))

        for thr in self.sock_threads:
            thr.stop()
            thr.join()

        if self.sock:
            self.sock.close()
            self.sock = None

    def run(self):
        """ Accept an incoming connection.
        Start a new SocketServerThread that will handle the communication. """
        print('Starting socket server (host {}, port {})'.format(self.host, self.port))

        self.__stop = False
        while not self.__stop:
            self.sock.settimeout(1)
            try:
                client_sock, client_addr = self.sock.accept()
            except socket.timeout:
                client_sock = None

            if client_sock:
                client_thr = SocketServerThread(client_sock, client_addr, self.counter)
                self.counter += 1
                self.sock_threads.append(client_thr)
                client_thr.start()
        self.close()

    def stop(self):
        self.__stop = True

class SocketServerThread(Thread):
    def __init__(self, client_sock, client_addr, number):
        """ Initialize the Thread with a client socket and address """
        Thread.__init__(self)
        self.client_sock = client_sock
        self.client_addr = client_addr
        self.number = number

    def run(self):
        print("[Thr {}] SocketServerThread starting with client {}".format(self.number, self.client_addr))
        self.__stop = False
        while not self.__stop:
            if self.client_sock:
                # Check if the client is still connected and if data is available:
                try:
                    rdy_read, rdy_write, sock_err = select.select([self.client_sock,], [self.client_sock,], [], 5)
                except select.error as err:
                    print('[Thr {}] Select() failed on socket with {}'.format(self.number,self.client_addr))
                    self.stop()
                    return

                if len(rdy_read) > 0:
                    read_data = self.client_sock.recv(1024)

                    # Check if socket has been closed
                    if len(read_data) == 0:
                        print('[Thr {}] {} closed the socket.'.format(self.number, self.client_addr))
                        self.stop()
                    else:
                        # Strip newlines just for output clarity
                        print(bcolors.blue)
                        print('[Thr {}] Received:'.format(self.number, ))#read_data.rstrip()
                        print(read_data.decode('cp1251'))
                        print(bcolors.reset)

                        # Проверка полученных данных на тип
                        try:
                            data = json.loads(read_data)
                        except json.decoder.JSONDecodeError as err:
                            print('JSON error')
                            continue

                        if type(data) == dict:
                            if 'msg_type' in data:
                                print(data['msg_type'])
                                if data['msg_type'] == 'REQUEST_DEVICE_LIST':
                                    # read example DEVICE_LIST
                                    f = open('device_list.json', 'r')
                                    print(bcolors.green + f.read() + bcolors.reset)
                                    f.seek(0)
                                    for l in f:                                        
                                        self.client_sock.send(bytes(l, 'cp1251'))
                                    f.close()
                                elif data['msg_type'] == 'REQUEST_SETUP_FULL':
                                    # read example REQUEST_SETUP_FULL
                                    f = open('device_setup_full.json', 'r')
                                    print(bcolors.green + f.read()  + bcolors.reset)
                                    f.seek(0)
                                    for l in f:                                        
                                        self.client_sock.send(bytes(l, 'cp1251'))
                                    f.close()
                                elif data['msg_type'] == 'REQUEST_SETUP_VALUES':
                                    # read example REQUEST_SETUP_VALUES
                                    f = open('device_setup_values.json', 'r')
                                    print(bcolors.green + f.read()  + bcolors.reset)
                                    f.seek(0)
                                    for l in f:                                        
                                        self.client_sock.send(bytes(l, 'cp1251'))
                                    f.close()  
                                elif data['msg_type'] == 'REQUEST_CHANGE_VALUE':
                                    #REQUEST_CHANGE_VALUE  
                                    msg_id = data['msg_id']
                                    sender_dev_id = data['sender_dev_id']
                                    dest_dev_id = data['dest_dev_id']
                                    param_id = data['msg_body']['value_new']['param_id']
                                    param_value = data['msg_body']['value_new']['param_value']
                                    result = 'OK'
                                    
                                    '''
                                    # Проверка на возврат другого значения
                                    if param_id == 1001:
                                        param_value = 155
                                        result = 'Failed'
                                    '''

                                    #print(type(param_value))
                                    if type(param_value) == list:
                                        resp_str = '{\n"msg_type": "DEVICE_VALUE_CONFIRM",\n\
                                            "msg_id": %d,\n\
                                            "sender_dev_id": %d,\n\
                                            "dest_dev_id": %d,\n\
                                            "msg_body": {\n\
                                            "value_confirm": {\n\
                                            "msg_id_confirm": %d,\n\
                                            "result": "%s",\n\
                                            "param_id": %d,\n\
                                            "new_value": [' % (msg_id+1, dest_dev_id, sender_dev_id, msg_id, result, param_id)
                                        i = 0
                                        for x in param_value:
                                            if i == 0:
                                                resp_str = resp_str + '%d'%(x)
                                                i = 1
                                            else:
                                                resp_str = resp_str + ', %d'%(x)
                                        resp_str = resp_str + ']\n}\n}\n}'   
                                        print(bcolors.green + resp_str.replace(' ', '') + bcolors.reset)
                                        self.client_sock.send(bytes(resp_str, 'cp1251'))   

                                    elif type(param_value) == int:
                                        resp_str = '{\n"msg_type": "DEVICE_VALUE_CONFIRM",\n\
                                            "msg_id": %d,\n\
                                            "sender_dev_id": %d,\n\
                                            "dest_dev_id": %d,\n\
                                            "msg_body": {\n\
                                            "value_confirm": {\n\
                                            "msg_id_confirm": %d,\n\
                                            "result": "%s",\n\
                                            "param_id": %d,\n\
                                            "new_value":%d\n\
                                            }\n}\n}' % (msg_id+1, dest_dev_id, sender_dev_id, msg_id, result, param_id, param_value)
                                        print(bcolors.green + resp_str.replace(' ', '')  + bcolors.reset)
                                        self.client_sock.send(bytes(resp_str, 'cp1251'))

                                    elif type(param_value) == float:
                                        resp_str = '{\n"msg_type": "DEVICE_VALUE_CONFIRM",\n\
                                            "msg_id": %d,\n\
                                            "sender_dev_id": %d,\n\
                                            "dest_dev_id": %d,\n\
                                            "msg_body": {\n\
                                            "value_confirm": {\n\
                                            "msg_id_confirm": %d,\n\
                                            "result": "%s",\n\
                                            "param_id": %d,\n\
                                            "new_value":%f\n\
                                            }\n}\n}' % (msg_id+1, dest_dev_id, sender_dev_id, msg_id, result, param_id, param_value)
                                        print(bcolors.green + resp_str.replace(' ', '')  + bcolors.reset)
                                        self.client_sock.send(bytes(resp_str, 'cp1251'))
            else:
                print("[Thr {}] No client is connected, SocketServer can't receive data".format(self.number))
                self.stop()
        self.close()

    def stop(self):
        self.__stop = True

    def close(self):
        """ Close connection with the client socket. """
        if self.client_sock:
            print('[Thr {}] Closing connection with {}'.format(self.number, self.client_addr))
            self.client_sock.close()        


if __name__ == "__main__":
    # Start socket server, stop it after a given duration
    #duration = 2 * 600
    server = SocketServer()
    server.start()
    #time.sleep(duration)
    #server.stop()
    #server.join()
    #print('End.')