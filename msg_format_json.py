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

class device_params():
    def __init__(self, msg_id, sender_dev_id, dest_dev_id, msg_body):
        self.msg_type = 'DEVICE_SETUP_FULL'
        self.msg_id = msg_id
        self.sender_dev_id = sender_dev_id
        self.dest_dev_id = dest_dev_id
        self.msg_body = msg_body

class device_list_msg_body():
    def __init__(self, device_list):
        self.device_list = device_list

class device_list():
    def __init__(self, msg_id, sender_dev_id, dest_dev_id, device_list):
        self.msg_type = 'DEVICE_LIST'
        self.msg_id = msg_id
        self.sender_dev_id = sender_dev_id
        self.dest_dev_id = dest_dev_id
        self.msg_body = device_list_msg_body(device_list)

class device_list_item():
    def __init__(self, dev_id = 0, dev_type = '', dev_name = '', dev_hw_ver = '', dev_fw_ver = '', fw_date = '', param_uuid = ''):
        self.dev_id = dev_id
        self.dev_type = dev_type
        self.dev_name = dev_name
        self.dev_hw_ver = dev_hw_ver
        self.dev_fw_ver = dev_fw_ver
        self.fw_date = fw_date
        self.param_uuid = param_uuid  

def msg_parse_json(self, data):
    if type(data) == dict:
        if 'msg_type' in data:
            print(data['msg_type'])
            if data['msg_type'] == 'REQUEST_DEVICE_LIST':
                # read DEVICE_LIST
                f = open('devices/devices_cfg.json', 'r')
                read_data = f.read()
                f.close()
                # Проверка полученных данных                        
                try:
                    data3 = json.loads(read_data)
                except json.decoder.JSONDecodeError as err:
                    print('JSON error')
                    return
                #print(data)
                if 'devices_to_check' in data3:
                    dev_item_array = []
                    for d in data3['devices_to_check']:
                        if d['access_via'] == 'file':
                            print(bcolors.cyan + 'reading file %s'%(d['file_name'],) + bcolors.reset)
                            
                            f = open('devices/%s'%(d['file_name'],), 'r')
                            read_data = f.read()
                            f.close()
                            # Проверка полученных данных                        
                            try:
                                data2 = json.loads(read_data)
                            except json.decoder.JSONDecodeError as err:
                                print('JSON error')
                                return
                            d_list_item = device_list_item()
                            if 'dev_info' in data2:
                                d_list_item.dev_id = data2['dev_info']['dev_id']
                                d_list_item.dev_type = data2['dev_info']['dev_type']
                                #d_list_item.dev_name = data2['dev_info']['dev_name']
                                d_list_item.dev_name = data2['dev_info']['dev_name'] + '  | id: ' + str(data2['dev_info']['dev_id']) + '  | file'
                                d_list_item.dev_hw_ver = data2['dev_info']['dev_hw_ver']
                                d_list_item.dev_fw_ver = data2['dev_info']['dev_fw_ver']
                                d_list_item.fw_date = data2['dev_info']['fw_date']
                                d_list_item.param_uuid = data2['dev_info']['param_uuid']
                                dev_item_array.append(d_list_item)    
                                self.found_devices.append({'dev_id': data2['dev_info']['dev_id'], 'filename': 'devices/%s'%(d['file_name'],)})                            

                        elif d['access_via'] == 'com_port':
                            print(bcolors.cyan + 'reading com port' + bcolors.reset)
                        elif d['access_via'] == 'socket':
                            print(bcolors.cyan + 'reading socket' + bcolors.reset)
                    self.msg_id += 1    
                    dl = device_list(self.msg_id, 0, data['dest_dev_id'], dev_item_array)
                    resp = json.dumps(dl, default=lambda o: o.__dict__, sort_keys=False, indent=4)
                    print(bcolors.green + resp + bcolors.reset)
                    self.client_sock.send(bytes(resp, 'cp1251'))

            elif data['msg_type'] == 'REQUEST_SETUP_FULL':
                # read example REQUEST_SETUP_FULL
                print(bcolors.yellow + 'read file') 
                print (self.found_devices)
                print(bcolors.reset)
                for fd in self.found_devices:
                    if 'dev_id' in fd:                        
                        if fd['dev_id'] == data['dest_dev_id']:
                            f = open(fd['filename'], 'r')
                            try:
                                demo_file_json = json.loads(f.read())
                            except json.decoder.JSONDecodeError as err:
                                print('JSON error')
                                return
                            dp = device_params(data['msg_id'], data['dest_dev_id'], data['sender_dev_id'], demo_file_json)  
                            resp = json.dumps(dp, default=lambda o: o.__dict__, sort_keys=False, indent=4)
                            print(bcolors.green + resp + bcolors.reset)                
                            f.seek(0)
                            self.client_sock.send(bytes(resp, 'cp1251'))
                                
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
                self.msg_id +=1
                msg_id_confirm = data['msg_id']
                sender_dev_id = data['sender_dev_id']
                dest_dev_id = data['dest_dev_id']
                param_id = data['msg_body']['value_new']['param_id']
                param_value = data['msg_body']['value_new']['param_value']
                result = 'OK'

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
                        "new_value": [' % (self.msg_id, dest_dev_id, sender_dev_id, msg_id_confirm, result, param_id)
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
                        }\n}\n}' % (self.msg_id, dest_dev_id, sender_dev_id, msg_id_confirm, result, param_id, param_value)
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
                        }\n}\n}' % (self.msg_id, dest_dev_id, sender_dev_id, msg_id_confirm, result, param_id, param_value)
                    print(bcolors.green + resp_str.replace(' ', '')  + bcolors.reset)
                    self.client_sock.send(bytes(resp_str, 'cp1251'))
