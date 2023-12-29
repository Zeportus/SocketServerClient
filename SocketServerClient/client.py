import socket
import json 
from threading import Thread, Event
import time

class Client:
    def __init__(self, path_to_servers_json: str) -> None:
        self.path_to_servers_json = path_to_servers_json
        self.servers_info = {}
        self._cmd_dict = {
            'show': self.show_servers,
            'disconnect': self.disconnect_from_server,
            'connect_raw': self.connect_raw_to_server,
            'connect': self.connect_to_server,
            'cmd': self.cmd_transmission,
            'help': self.show_help
        }
        self.client_socket = None
        self.print_event = Event()
        self._cmd_cache = {}
        self.last_update = 0
        self.refresh_servers_info()

    def refresh_servers_info(self):
        with open(self.path_to_servers_json) as f:
            self.servers_info = json.load(f)
        
    def show_servers(self):
        self.refresh_servers_info()
        print('Name         Host        Port')
        for server_name, server_addr in self.servers_info.items():
            print(server_name, server_addr['host'], server_addr['port'], sep=' '*5)

    def disconnect_from_server(self):
        if not self.client_socket:
            print('You havent connection now')
            return
        self.cmd_transmission('disconnect')

    def connect_to_server(self, server_name):
        if not self.client_socket or self.client_socket.fileno() == -1:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = self.servers_info[server_name]['host']
        port = self.servers_info[server_name]['port']
        self.client_socket.connect((host, port))
        print(f'You have connected to server "{server_name}"')
        th = Thread(target=self.read_socket)
        th.start()
    
    def connect_raw_to_server(self, host, port):
        if not self.client_socket or self.client_socket.fileno() == -1:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, int(port)))
        print(f'You have connected to server host = {host}; port = {port}')
        th = Thread(target=self.read_socket)
        th.start()

    def execute_cmd(self, cmd: str):
        if not cmd: 
            self.show_error()
            return
        action, *args = cmd.split(maxsplit=1)
        if action == 'connect_raw':
            args = args[0].split()
        func_to_complete = self._cmd_dict.get(action, self.show_error)
        func_to_complete(*args)
    
    def cmd_transmission(self, cmd: str):
        if not self.client_socket or self.client_socket.fileno() == -1:
            print('Connect to a server firstly')
            return

        if cmd in self._cmd_cache and time.time() - self.last_update < 30:
            print(self._cmd_cache[cmd])
        else:
            self.client_socket.send(cmd.encode())
            self.print_event.wait()
            self.print_event.clear()
            self.last_update = time.time()

    def read_socket(self):
        while True:
            if self.client_socket.fileno() == -1:
                break
            data = self.client_socket.recv(1024).decode()
            if data == '::DISCONNECT_BY_SERVER::':
                self.client_socket.close()
                print('You have disconnected from server, because it has shutdowned')
                break
            elif data == '::DISCONNECT_BY_USER::':
                self.client_socket.close()
                print('You have disconnected from server')
                break
            cmd, data = data.split('::')
            self._cmd_cache[cmd] = data
            print(data)
            self.print_event.set()
        self.print_event.set()
    
    def show_error(self, *args):
        print('No such command')

    def show_help(self):
        help = '''
show - shows available servers
connect [server_name] - connect to chosed server_name
connect_raw [server_host] [server_port] - connect with host and port
cmd [server_command] [server_arg1, server_arg2, ...] - execute server command
cmd help - show available commands on connected server
disconnect - disconnect from current server
help - show this message
'''
        print(help)


client = Client('servers.json')
print('You can type help, to view commands')
while True:
    print('Input command:')
    client.execute_cmd(input())
    print()