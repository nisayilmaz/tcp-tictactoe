import socket
import threading
import ast
import random
import json
HOST = "127.0.0.1" 
PORT =  7777

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(2)

player_sockets = []
watching_sockets = []
num_players = 0
board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
signs = ["X", "O"]
player_signs = []
data_dict = {}
status = {"status":0, "winner":""}
turn = 0

def check_row():
    global board
    win = 0
    winner = ""
    for i in range(0, 3):
        if board[i][1] == board[i][0] == board[i][2] == 1 or board[i][1] == board[i][0] == board[i][2] == 2:
            win = 1
            winner = board[i][1]
            break
    
    return(win, winner)
def check_column():
    global board
    win = 0
    winner = ""
    for j in range(0, 3):
        if board[1][j] == board[0][j] == board[2][j] == 1 or board[1][j] == board[0][j] == board[2][j] == 2:
            win = 1
            winner = board[1][j]
            break
    
    return(win, winner)

def check_diagonal():
    global board
    win = 0
    winner = ""
    if board[0][0] == board[1][1] == board[2][2] == 1 or board[0][0] == board[1][1] == board[2][2] == 2: 
        win = 1
        winner = board[0][0]
    elif board[0][2] == board[1][1] == board[2][0] == 1 or board[0][2] == board[1][1] == board[2][0] == 2:
        win = 1
        winner = board[0][2]
    return(win, winner)

def check_draw():
    global board
    draw = 1
    for i in range(0,3):
        for j in range(0, 3):
            if board[i][j] == 0:
                draw = 0
                break

    return (draw, "draw")

def check_move(x,y):
    global board
    return board[x][y] == 0
def game():    
    result = check_column()
    if result[0]:
        return result
    
    result = check_row()
    if result[0]:
        return result
    
    result = check_diagonal()
    if result[0]:
        return result
    
    result = check_draw()
    if result[0]:
        return result
    result = (0, "")
    return result

def handle_player(client_socket):
    global board,turn
    while True:
        try:
            data = client_socket.recv(1024)
            print(data)
            data_dict = ast.literal_eval(data.decode("utf-8"))
            move = data_dict.get("move")
            if move:
                x = int(move.split("$")[0])
                y = int(move.split("$")[1])
                sign = data_dict.get("move_sign")
                if sign == "X":
                    sign = 1
                elif sign == "O":
                    sign = 2
                if check_move(x,y):
                    board[x][y] = sign
                    result = game()
                    turn = turn + 1 
                else:
                    print("invalid move")
                if result[0] == 1 and result[1] != "":
                    if result[1] == "draw":
                        status["status"] = 1
                        status["winner"] = "draw"
                    else:
                        winner = result[1]
                        status["status"] = 1
                        status["winner"] = winner
            index = player_sockets.index(client_socket)
            opponent = player_sockets[1-index]
            data_dict.update(status)
            board_send = {
                "board" : json.dumps(board)
            }
            data_dict.update(board_send)
            data_dict.update({"turn":turn})
            opponent.send(bytes(str(data_dict), 'utf-8'))
            client_socket.send(bytes(str(data_dict), 'utf-8'))
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
        if num_players < 2:
            client_socket, addr = server_socket.accept()
            data = client_socket.recv(1024)
            data_dict = ast.literal_eval(data.decode("utf-8"))
            req = data_dict.get("requested", None)
            if req:
                if req == "player":
                    player_sockets.append(client_socket)
                    curr = player_sockets.index(client_socket)
                    details = {"sign": player_signs[curr] , "role": "player", "turn": turn}
                    client_socket.send(bytes(str(details), 'utf-8'))
                    num_players = num_players + 1
                    if num_players == 2:
                        all_s = player_sockets + watching_sockets
                        for socket_s in all_s:
                            socket_s.send(bytes(str({"game_started": True}), "utf-8"))
                    print(num_players)
                    client_thread = threading.Thread(target=handle_player, args=(client_socket,))
                    client_thread.start()
                elif req == "watcher":
                    details = {"role": "watcher", "turn": turn}
                    details.update({"board": json.dumps(board)})
                    client_socket.send(bytes(str(details), 'utf-8'))
                    print(f'Connected to client at {addr}')
                    watching_sockets.append(client_socket)
                    client_thread = threading.Thread(target=handle_watcher, args=(client_socket,))
                    client_thread.start()
            print(f'Connected to client at {addr}')
        elif num_players >= 2:
            client_socket, addr = server_socket.accept()
            details = {"role": "watcher", "turn": turn, "game_started" : True, "board":json.dumps(board)}
            client_socket.send(bytes(str(details), 'utf-8'))
            print(f'Connected to client at {addr}')
            watching_sockets.append(client_socket)
            status = {
                "game_started" : True
            }
            all_s = player_sockets + watching_sockets
            for socket_s in all_s:
                if socket_s is not client_socket:
                    socket_s.send(bytes(str(status), "utf-8"))
            client_thread = threading.Thread(target=handle_watcher, args=(client_socket,))
            client_thread.start()
        

