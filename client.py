import socket
import ast
import threading
import json
HOST = "127.0.0.1" 
PORT =  7777

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
    
def print_grid(game_grid):
    signs = [" ", "X", "O"]
    print("-------")
    for i in range(0,3):
        print("", end= "|")
        for j in range(0, 3):
            print(signs[game_grid[i][j]], end= "|")
        print("\n-------")


role = ""
sign = ""
turn =""
const = 1
signs = ["X", "O"]
game_fin = 0
started = 0

def process_input(data_dict, client_socket):
    global role, sign, turn, const, game_details, signs, game_fin, started
    role_server = data_dict.get("role", None)
    sign_server = data_dict.get("sign", None)
    board_server = data_dict.get("board", None)
    started_server = data_dict.get("game_started", None)
    status_server = data_dict.get("status", None)
    turn_msg = data_dict.get("turn_msg", None)
    conn_id = data_dict.get("conn_id", None)

    if started_server and started_server == True:
        started = started_server
    if board_server:
        board = json.loads(board_server)
        print_grid(board)
    if role_server:
        role = role_server
    if sign_server:
        sign = sign_server
        const = 1 - signs.index(sign)
    if turn_msg:
        turn = turn_msg
        if not game_fin:
            print(turn_msg, "Sign", sign)

    if status_server:
        winner = data_dict.get("winner")

        if status_server == -1:
            if turn != "Opponent's turn!":
                print(winner)           
        else:
            num = {1: "X", 2: "O"}
            res_txt = "Game over!\nResult: "
            game_fin = status_server
            if winner == "draw":
                res_txt = res_txt + "Draw"
            else:
                res_txt = res_txt + "Winner " + num.get(winner)
            if game_fin:
                print(res_txt)

    if turn == "Your turn!" and role == "player" and started and not game_fin:
        x = int(input("Enter x coordinate: "))
        y = int(input("Enter y coordinate: "))
        game_details = {}
        game_details["move"] = str(x) + "$" + str(y)
        game_details["move_sign"] = sign
        client_socket.send(bytes(str(game_details), "utf-8"))
    if conn_id:
        self_id = conn_id
        print("Your id:", self_id)
 
    if game_fin:
        client_socket.close()
    

while 1:
    try:
        data = client_socket.recv(1024)
        data = data.decode("utf-8")
        if data == "":
            break
        data_dict = ast.literal_eval(data)
        client_thread = threading.Thread(target=process_input, args=(data_dict, client_socket,))
        client_thread.start()
    except ConnectionAbortedError:
        break

client_socket.close()