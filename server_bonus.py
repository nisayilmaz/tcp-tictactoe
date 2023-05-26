import socket
import threading
import ast
import random
import json
import sys
HOST = "127.0.0.1" 
PORT =  int(sys.argv[1])

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
connections = {}
starts = -1

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
    valid = True
    if x < 0 or x > 2 or y < 0 or y > 2 or board[x][y] != 0:
        valid = False
    return valid
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
            if not data:
                break

            # convert the data back to dict
            data_dict = ast.literal_eval(data.decode("utf-8"))

            # handle player move
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
                    # check game status
                    if result[0] == 1 and result[1] != "":
                        if result[1] == "draw":
                            status["status"] = 1
                            status["winner"] = "draw"
                        else:
                            winner = result[1]
                            status["status"] = 1
                            status["winner"] = winner
                else:
                    status["status"] = -1
                    status["winner"] = "Invalid move, please make another move!"
            # data_dict contins info coming from the client, add status info,current board info
            data_dict.update(status)
            board_send = {
                "board" : json.dumps(board)
            }
            data_dict.update(board_send)

            # determine whose turn and send message 
            first_player = {}
            first_player.update(data_dict)
            second_player = {}
            second_player.update(data_dict)
            watcher_dict = {}
            watcher_dict.update(data_dict)
            if turn % 2 == 0:
                first_player["turn_msg"] = "Your turn!"
                second_player["turn_msg"] = "Opponent's turn!"
                watcher_dict["turn_msg"] = "Player" + str(player_sockets[starts]) + "'s turn"

            else:
                first_player["turn_msg"] = "Opponent's turn!"
                second_player["turn_msg"] = "Your turn!"
                watcher_dict["turn_msg"] = "Player" + str(player_sockets[1-starts]) + "'s turn"
            connections[player_sockets[starts]].send(bytes(str(first_player), 'utf-8'))
            connections[player_sockets[1 - starts]].send(bytes(str(second_player), 'utf-8'))
            
            for i in range(len(watching_sockets)):
                socket_w = connections[watching_sockets[i]] 
                socket_w.send(bytes(str(watcher_dict), 'utf-8'))

        except (ConnectionResetError, ConnectionAbortedError):
            pass

def handle_watcher(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            print(data)
            if not data:
                break

            for i in range(len(watching_sockets)):
                socket_w = connections[watching_sockets[i]] 
                socket_w.send(data) 
            for j in range(len(player_sockets)):
                socket_w = connections[player_sockets[j]] 
                socket_w.send(data)
            
        except (ConnectionResetError, ConnectionAbortedError):
            pass



while(1):
    number = random.randint(0,1000) % 2
    player_signs.insert(0, signs[number])
    player_signs.insert(1, signs[1 - number])
    starts = random.randint(0,1000) % 2
    while 1:
        if num_players < 2:
            client_socket, addr = server_socket.accept()
            data = client_socket.recv(1024)
            data_dict = ast.literal_eval(data.decode("utf-8"))
            req = data_dict.get("requested", None)
            conn_id =  random.randint(0,1000)
            while conn_id in connections.keys():
                conn_id =  random.randint(0,1000)

            if req:
                if req == "player":
                    player_sockets.append(conn_id)
                    curr = player_sockets.index(conn_id)
                    connections[conn_id] = client_socket
                    if curr == starts:
                        details = {"sign": player_signs[curr] , "role": "player","conn_id": conn_id, "turn_msg":"Your turn!"}
                    else:
                        details = {"sign": player_signs[curr] , "role": "player", "conn_id": conn_id, "turn_msg":"Opponent's turn!"}
                    
                    print("A player has connected with id:", conn_id, "and sign", player_signs[curr])

                    client_socket.send(bytes(str(details), 'utf-8'))
                    num_players = num_players + 1
                    if num_players == 2:
                        for socket_s in connections.values():
                            socket_s.send(bytes(str({"game_started": True}), "utf-8"))
                    client_thread = threading.Thread(target=handle_player, args=(client_socket,))
                    client_thread.start()
                elif req == "watcher":
                    details = {"role": "watcher", "conn_id": conn_id }
                    details.update({"board": json.dumps(board)})
                    client_socket.send(bytes(str(details), 'utf-8'))
                    print("A watcher has connected with id:", conn_id)
                    watching_sockets.append(conn_id)
                    connections[conn_id] = client_socket
                    client_thread = threading.Thread(target=handle_watcher, args=(client_socket,))
                    client_thread.start()
                if num_players == 2:
                    print("Game started")
                    for id in watching_sockets:
                        connections[id].send(bytes(str({"turn_msg":"Player" + str(player_sockets[starts]) + "'s turn"}), "utf-8"))
        elif num_players >= 2:
            client_socket, addr = server_socket.accept()
            conn_id =  random.randint(0,1000)
            while conn_id in connections.keys():
                conn_id =  random.randint(0,1000)
            curr = 0
            if turn % 2 == 0:
                curr = starts
            else :
                curr = 1 - starts

            details = {"role": "watcher","conn_id": conn_id, "board":json.dumps(board),  "game_started" : True, "turn_msg":"Player" + str(player_sockets[curr]) + "'s turn"}
            client_socket.send(bytes(str(details), 'utf-8'))
            watching_sockets.append(conn_id)
            connections[conn_id] = client_socket

            status = {
                "game_started" : True,
                
            }
            for id, socket_s in connections.items():
                if socket_s is not client_socket:
                    socket_s.send(bytes(str(status), "utf-8"))
                
            client_thread = threading.Thread(target=handle_watcher, args=(client_socket,))
            client_thread.start()
        

