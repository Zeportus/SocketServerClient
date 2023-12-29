from server import Server, Server1, Server2
from multiprocessing import Process, current_process, Pipe
from server_logger import ServerLogger
import socket
from threading import Thread
import signal
import sys
import json
from copy import deepcopy
from time import sleep


print(current_process().pid)
def socket_worker(server: Server, client_socket: socket.socket, client_addr, must_die):
    client_socket.settimeout(5)
    while True:            
        try:
            cmd = client_socket.recv(1024).decode()
        except:
            if must_die[0]:
                server.send_data(client_socket, '::DISCONNECT_BY_SERVER::')
                break
        else:
            if cmd == 'disconnect': 
                server.send_data(client_socket, '::DISCONNECT_BY_USER::')
                break
            answer = server.execute_cmd(cmd)
            server.send_data(client_socket, f'{cmd}::{answer}')
    server.close_client(client_socket, client_addr)
    must_die[1] += 1

def server_worker(server: Server):
    # 0 index determines must threads die or not.
    # 1 index determines how much threads already died
    threads_must_die = [False, 0]
    threads_count = 0
    send_pipe, receive_pipe = Pipe()
    server.set_pipe(send_pipe)
    server_logger = ServerLogger(f'{server.server_name}_logger', receive_pipe)
    log_prcs = Process(target=server_logger.log_worker)
    log_prcs.start()
    def stop_worker(sig, frame):
        server.close()
        threads_must_die[0] = True
        # Wait until all threads died and only after that
        # terminate log servers, because there is nothing 
        # to be logged
        while threads_count != threads_must_die[1]:
            pass
        log_prcs.terminate()
        log_prcs.join()
        sys.exit(0)

    
    signal.signal(signal.SIGTERM, stop_worker)
    server.bind_socket()
    while True:
        client_socket, client_addr = server.wait_for_request()
        thr = Thread(target=socket_worker, args=(server, client_socket, client_addr, threads_must_die))
        thr.start()
        threads_count += 1

class ServerType:
    SERVER1 = Server1
    SERVER2 = Server2
    
    type_dict = {
        'SERVER1': SERVER1,
        'SERVER2': SERVER2
    }

    @classmethod
    def get_type_by_str(cls, server_type_str):
        return cls.type_dict[server_type_str]


class ServerManager:
    def __init__(self) -> None:
        self.servers = {}
        self.servers_prcss = {}
        self.reserved_servers = []
        self._cmd_dict = {
            'show': self.show_servers,
            'create': self.create_server,
            'run': self.run_server,
            'stop': self.stop_server,
            'help': self.show_help,
            'exit': self.exit
        }
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        for server_name, server_prcs in self.servers_prcss.items():
            if not server_prcs.is_alive():
                continue
            server_prcs.terminate()
            server_prcs.join()
            print(f'Server "{server_name}" has beautiful terminated')
        print('Oh shit i am dead')
        self.servers.clear()
        self.log_server()
        sys.exit(0)

    
    def create_server(self, server_type, name: str, host: str, port: int):
        if isinstance(server_type, str):
            server_type = ServerType.get_type_by_str(server_type)

        if server_type in self.reserved_servers:
            print(f'Server type "{server_type.__name__}" is already created')
            return

        if name in self.servers:
            print(f'Server name "{name}" is already used by other server')
            return
        
        new_server = server_type(name, host, int(port))
        self.reserved_servers.append(server_type)
        self.servers[name] = new_server
        self.servers_prcss[name] = Process(target=server_worker, args=(new_server,))

    def run_server(self, name):
        if name in self.servers_prcss:
            prcss = self.servers_prcss[name]
            if not prcss.is_alive():
                prcss.start()
                self.log_server()
            else:
                print(f'Server with name "{name}" already running')
        else:
            print(f'Server with name "{name}" does not exist')
             
    def stop_server(self, name):
        if name in self.servers_prcss:
            prcss = self.servers_prcss[name]
            if prcss.is_alive():
                prcss.terminate()
                prcss.join()
                self.servers_prcss[name] = Process(target=server_worker, args=(self.servers[name],))
                self.log_server()
            else:
                print(f'Server with name "{name}" already stopped')
        else:
            print(f'Server with name "{name}" does not exist')

    def log_server(self):
        buffer = {}
        for server_name, prcss in self.servers_prcss.items():
            if not prcss.is_alive(): continue
            server = self.servers[server_name]
            buffer[server_name] = {'host': server.host, 'port': server.port}
        with open('servers.json', 'w') as f:
            json.dump(buffer, f)

    def execute_cmd(self, cmd: str):
        if not cmd: 
            self.show_error()
            return
        action, *args = cmd.split()
        func_to_complete = self._cmd_dict.get(action, self.show_error)
        func_to_complete(*args)

    def show_error(self, *args):
        print('No such command')

    def show_servers(self):
        for server_name, server_prcs in self.servers_prcss.items():
            status = 'running' if server_prcs.is_alive() else 'stopped'
            print(f'Server "{server_name}" is {status}')
    
    def exit(self):
        self.signal_handler(0, 0)
                  
    def show_help(self):
        help = '''
create [SERVERTYPE] [name] [host] [port] - create server
run [name] - run server with chosed name
stop [name] - stop server with chosed name
show - shows all created servers and their status
exit - exit ServerManager and drop all servers
help - show this message
'''
        print(help)
        
        
