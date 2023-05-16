import socket
import threading
import ast
import random
HOST = "127.0.0.1" 
PORT =  7777

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(2)

player_sockets = []
watching_sockets = []
num_people = 0
signs = ["X", "O"]
player_signs = []
data_dict = {}
status = {"status":0, "winner":""}
def handle_player(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            print(data)
            data_dict = ast.literal_eval(data.decode("utf-8"))
            result = data_dict.get("result", None)
            if result:
                result = result.split("$")
                if result[0] == "1" and result[1] != "":
                    if result[1] == "draw":
                        status["status"] = 1
                        status["winner"] = "draw"
                    else:
                        winner = result[1]
                        status["status"] = 1
                        status["winner"] = winner
                    client_socket.send(bytes(str(status), 'utf-8'))
            index = player_sockets.index(client_socket)
            opponent = player_sockets[1-index]
            data_dict.update(status)
            opponent.send(bytes(str(data_dict), 'utf-8'))
            for i in range(len(watching_sockets)):
                socket_w = watching_sockets[i] 
                socket_w.send(bytes(str(data_dict), 'utf-8'))

            if not data:
                break
        except (ConnectionResetError, ConnectionAbortedError):
            pass

def handle_watcher(client_socket):
    while True:
        data = client_socket.recv(1024)
        print("Watcher sent reaction: ", data)
        for i in range(len(watching_sockets)):
            socket_w = watching_sockets[i] 
            socket_w.send(data)
        for j in range(len(player_sockets)):
            socket_w = player_sockets[j] 
            socket_w.send(data)
        if not data:
            break



while(1):
    number = random.randint(0,1000) % 2
    player_signs.insert(0, signs[number])
    player_signs.insert(1, signs[1 - number])
    while 1:
        if num_people < 2:
            client_socket, addr = server_socket.accept()
            print(f'Connected to client at {addr}')
            player_sockets.append(client_socket)
            curr = player_sockets.index(client_socket)
            details = {"sign": player_signs[curr] , "role": "player", "turn": 0}
            client_socket.send(bytes(str(details), 'utf-8'))
            client_thread = threading.Thread(target=handle_player, args=(client_socket,))
            client_thread.start()
            num_people = num_people + 1
        elif num_people >= 2:
            client_socket, addr = server_socket.accept()
            details = {"role": "watcher", "turn": 0}
            client_socket.send(bytes(str(details), 'utf-8'))
            print(f'Connected to client at {addr}')
            watching_sockets.append(client_socket)
            client_thread = threading.Thread(target=handle_watcher, args=(client_socket,))
            client_thread.start()
            num_people = num_people + 1
        

