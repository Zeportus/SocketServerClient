from server import Server
from multiprocessing.connection import Connection
from multiprocessing import current_process
from datetime import datetime
import signal
import sys


class ServerLogger:
    def __init__(self, server_name: str, recv_pipe: Connection) -> None:
        self.server_name = server_name
        self.recv_pipe = recv_pipe
    
    def stop_worker(self, sig, frame):
            with open(f'{self.server_name}.log', 'a') as f:
                f.write('\n' + '-'*100 + '\n\n')
            sys.exit(0)

    def log_worker(self):    
        signal.signal(signal.SIGTERM, self.stop_worker)
        while True:
            info = self.recv_pipe.recv()
            time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            with open(f'{self.server_name}.log', 'a') as f:
                f.write(f'[{time}]    {info}\n')
    