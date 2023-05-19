import socket
import ast
import threading
HOST = "127.0.0.1" 
PORT =  7777

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))


game_grid= [[" "," "," "],[" "," "," "],[" "," "," "]]

def check_row():
    win = 0
    winner = ""
    for i in range(0, 3):
        if game_grid[i][1] == game_grid[i][0] == game_grid[i][2] == "X" or game_grid[i][1] == game_grid[i][0] == game_grid[i][2] == "O":
            win = 1
            winner = game_grid[i][1]
            break
    
    return(win, winner)
def check_column():
    win = 0
    winner = ""
    for j in range(0, 3):
        if game_grid[1][j] == game_grid[0][j] == game_grid[2][j] == "X" or game_grid[1][j] == game_grid[0][j] == game_grid[2][j] == "O":
            win = 1
            winner = game_grid[1][j]
            break
    
    return(win, winner)

def check_diagonal():
    win = 0
    winner = ""
    if game_grid[0][0] == game_grid[1][1] == game_grid[2][2] == "X" or game_grid[0][0] == game_grid[1][1] == game_grid[2][2] == "O": 
        win = 1
        winner = game_grid[0][0]
    elif game_grid[0][2] == game_grid[1][1] == game_grid[2][0] == "X" or game_grid[0][2] == game_grid[1][1] == game_grid[2][0] == "O":
        win = 1
        winner = game_grid[0][2]
    return(win, winner)

def check_draw():
    draw = 1
    for i in range(0,3):
        for j in range(0, 3):
            if game_grid[i][j] == " ":
                draw = 0
                break

    return (draw, "draw")

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
    
input_lock = threading.Lock()

def play_turn(sign):
    input_lock.acquire()
    x = int(input("Enter x: "))
    y = int(input("Enter y: "))
    input_lock.release()
    while x == "" or y == "" or x >= 3 or y >= 3 or game_grid[x][y] != " " :
        print("enter another set of coordinates")
        input_lock.acquire()
        x = int(input("Enter x: "))
        y = int(input("Enter y: "))
        input_lock.release()
    
    game_grid[x][y] = sign
    return (x,y)
    
def print_grid():
    print("-------")
    for i in range(0,3):
        print("", end= "|")
        for j in range(0, 3):
            print(game_grid[i][j], end= "|")
        print("\n-------")


role = ""
sign = ""
turn = 0
const = 1
game_details = {"move": "", "turn": 0, "result":""}
signs = ["X", "O"]
game_fin = 0

def process_input(data_dict, client_socket):
    global role, sign, turn, const, game_details, signs, game_fin
    turn = data_dict.get("turn",None)
    reaction = data_dict.get("reaction",None)
    role_server = data_dict.get("role",None)
    move = data_dict.get("move",None)
    sign_server = data_dict.get("sign",None)
    status = data_dict.get("status",None)
    winner = data_dict.get("winner",None)
    if reaction:
        print("Watcher has sent reaction: {}".format(reaction))
    if role_server:
        role = role_server
    if sign_server:
        sign = sign_server
        const = 1 - signs.index(sign)
    if move:
        x = int(move.split("$")[0])
        y = int(move.split("$")[1])
        opponent_sign = data_dict.get("move_sign")
        game_grid[x][y] = opponent_sign
        print_grid()
    if status and winner:
        game_fin = 1
        if winner == "draw":
            print("Game has ended with a draw.")
        else:
            print('Game has ended and the winner is {}'.format(winner))
    if role == "watcher":
        reaction = input("Enter reaction (press enter if none)")
        if reaction:
            details = {"reaction" : reaction}
            client_socket.send(bytes(str(details), "utf-8"))

    if turn is not None and role == "player":
        turn = int(turn)
        if turn % 2 == const and not game_fin:
            (x,y)=play_turn(sign)
            print_grid()
            result = game()
            turn = turn + 1
            game_details["move"] = str(x) + "$" + str(y)
            game_details["move_sign"] = sign
            game_details["turn"] = turn
            game_details["result"] = str(result[0]) + "$" + str(result[1])
            client_socket.send(bytes(str(game_details), "utf-8"))


while 1:
    data = client_socket.recv(1024)
    data = data.decode("utf-8")
    if data == "":
        break

    data_dict = ast.literal_eval(data)
    client_thread = threading.Thread(target=process_input, args=(data_dict, client_socket,))
    client_thread.start()
    

   
    
            


client_socket.close()