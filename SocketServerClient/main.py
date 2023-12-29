from server_manager import ServerManager

        
manager = ServerManager()

print('You can type help, to view commands')
while True:
    print('Input command:')
    manager.execute_cmd(input())
    print()
