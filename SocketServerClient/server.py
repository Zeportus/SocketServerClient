import socket
from screeninfo import get_monitors
import PIL.ImageGrab
from multiprocessing import current_process
from multiprocessing.connection import Connection


class Server:
    def __init__(self, server_name: str, host: str, port: int) -> None:
        self.server_name = server_name
        self.host = host
        self.port = port
        # cmd_dict contains commands and linked handlers, which sets
        # in child server classes
        self._cmd_dict = {'help': self.show_help}

    def set_pipe(self, log_pipe):
        self.log_pipe = log_pipe

    def print(self, msg):
        self.log_pipe.send(msg)

    def bind_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.print(f'Server "{self.server_name}" starts listen on {self.host}:{self.port}')
    
    def wait_for_request(self):
        """Server starts listen and after client's request
        return client socket and client address in tuple"""

        client_socket, client_addr = self.server_socket.accept()
        self.print(f'Client {client_addr[0]}:{client_addr[1]} has connected to server "{self.server_name}"')
        return (client_socket, client_addr)
    
    def execute_cmd(self, cmd: str):
        action, *args = cmd.split()
        self.print(f'Server "{self.server_name}" starts executing command {action}')
        func_to_exc = self._cmd_dict.get(action, self.get_error)
        return func_to_exc(*args)

    def close_client(self, client_socket: socket.socket, client_addr):
        client_socket.close()
        self.print(f'Client socket {client_addr[0]}:{client_addr[1]} has closed')
    
    def close(self):
        self.server_socket.close()
        self.print(f'Server "{self.server_name}" socket has closed')
    
    def send_data(self, client_socket: socket.socket, data: str):
        client_socket.send(data.encode())
    
    def get_error(self):
        return f'No such command on {self.server_name}'

    def show_help(self):
        raise NotImplementedError


class Server1(Server):
    def __init__(self, server_name: str, host: str, port: int) -> None:
        super().__init__(server_name, host, port)

        # Set here action name and his handler.
        # cmd_recognizer will use it to determine
        # which func needs to run
        self._cmd_dict.update({
            'moninfo': self.get_monitor_info,
            'pxlcolor': self.get_pixel_color
        })

    def get_monitor_info(self):
        monitor_info = get_monitors()[0]
        data = f'Monitor width: {monitor_info.width}\nMonitor height: {monitor_info.height}'
        self.print(f'Server "{self.server_name}" has gave monitor info')
        return data
    
    def get_pixel_color(self, x, y):
        rgb = PIL.ImageGrab.grab().load()[1919, 1079]
        data = f'R: {rgb[0]} G: {rgb[1]} B: {rgb[2]}'
        self.print(f'Server "{self.server_name}" has gave color of pixel with coords: {x}, {y}')
        return data
    
    def show_help(self):
        help = '''
moninfo - shows monitor width and height
pxlcolor [arg_x] [arg_y] - shows rgb of coordinates
help - shows this menu
'''
        self.print(f'Server "{self.server_name}" has gave help menu')
        return help

class Server2(Server):
    def __init__(self, server_name: str, host: str, port: int) -> None:
        super().__init__(server_name, host, port)

        # Set here action name and his handler.
        # cmd_recognizer will use it to determine
        # which func needs to run
        self._cmd_dict.update({
            'getpid': self.get_pid,
            'getsockfd': self.get_descriptor
        })

    def get_pid(self):
        pid = current_process().pid
        data = f'Server "{self.server_name}" PID is {pid}'
        self.print(f'Server "{self.server_name}" has gave his pid')
        return data
    
    def get_descriptor(self):
        fd = self.server_socket.fileno()
        data = f'Server "{self.server_name}" socket descriptor is {fd}'
        self.print(f'Server "{self.server_name}" has gave his socket descriptor')
        return data
    
    def show_help(self):
        help = '''
getpid - shows server proccess pid
getsockfd - shows socket descriptor of this server
help - shows this menu
'''
        self.print(f'Server "{self.server_name}" has gave help menu')
        return help