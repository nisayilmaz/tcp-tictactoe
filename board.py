import sys
import socket
import ast
import threading
import json
from tkinter import *
from tkinter import messagebox, ttk

HOST = "127.0.0.1"
PORT = 7777


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

############################################ UI ###############################################################
root = Tk()
root.title("GeeksForGeeks - Tic Tac Toe")
root.resizable(0, 0)
main_frame = Frame(root)
wait_frame = Frame(root)
game_end = Frame(root)

main_frame.grid(row = 0, column = 0, rowspan=4, columnspan=3, sticky ="nsew")
wait_frame.grid(row = 0, column = 0, rowspan=4, columnspan=3, sticky ="nsew")
game_end.grid(row = 0, column = 0, rowspan=4, columnspan=3, sticky ="nsew")

turn_label = ttk.Label(main_frame, text="Player 1's Turn", font=("Helvetica", 16))
turn_label.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

chat_frame = Frame(main_frame, width=200, height=300, bd=1, relief=SOLID)
chat_frame.grid(row=0, column=3, rowspan=4, columnspan=2, padx=10, pady=10)

chat_text = Text(chat_frame, width=30, height=15)
chat_text.grid(row=0, column=0,rowspan=3, padx=5, pady=5)

scrollbar = Scrollbar(chat_frame, command=chat_text.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
chat_text.config(yscrollcommand=scrollbar.set)

chat_input = Entry(chat_frame, width=30)
chat_input.grid(row=3, column=0, padx=10, pady=5)

lbl = ttk.Label(wait_frame, text="Welcome! Waiting for players...", font=("Helvetica", 20))
lbl.grid(row=0, column=0, columnspan=3, padx=10, pady=10)


def player():
    requested = {
        "requested" : "player"
    }
    client_socket.send(bytes(str(requested), "utf-8"))

def watcher():
    requested = {
        "requested" : "watcher"
    }
    client_socket.send(bytes(str(requested), "utf-8"))

player_btn = Button(wait_frame, text="Player", command=player)
player_btn.grid(row=3, column=1, padx=10, pady=5)

watcher_btn = Button(wait_frame, text="Watcher", command=watcher)
watcher_btn.grid(row=3, column=2, padx=10, pady=5)

wait_frame.tkraise()

#Button
b = [
     [0,0,0],
     [0,0,0],
     [0,0,0]]
 
role = ""
sign = ""
msg = ""
turn = 0
const = 1
game_details = {"move": ""}
signs = ["X", "O"]
game_fin = 0
self_id = 0
sender_id = 0

def updateBoard(board):
    num_to_s = ["", "X", "O"]
    global b
    for i in range(0,3):
        for j in range(0,3):
            b[i][j].configure(text= num_to_s[board[i][j]])

def updateChat(msg):
    global chat_text,sender_id, self_id
    chat_text.insert("end","User " + str(sender_id) + ": " + msg)

def sendMsg():
    global chat_input,client_socket,self_id
    msg = chat_input.get()
    chat_input.delete(0, END)
    msg = {
        "reaction" : msg + "\n", "sender_id": self_id
    }
    client_socket.send(bytes(str(msg), "utf-8"))

send_button = Button(chat_frame, text="Send", command=sendMsg)
send_button.grid(row=3, column=1, padx=10, pady=5)


def handle(data_dict):
    global role, sign, turn, const, game_details, signs, game_fin, board, can_process,res_txt, msg, sender_id, self_id
    can_process = 0
    turn_server = data_dict.get("turn", None)
    role_server = data_dict.get("role", None)
    sign_server = data_dict.get("sign", None)
    board_server = data_dict.get("board", None)
    reaction_server = data_dict.get("reaction", None)
    started = data_dict.get("game_started", None)
    status_server = data_dict.get("status", None)
    turn_msg = data_dict.get("turn_msg", None)
    conn_id = data_dict.get("conn_id", None)
    sender_server = data_dict.get("sender_id", None)

    if started and (started == True or started == "True"):
        main_frame.tkraise()
    if board_server:
        board = json.loads(board_server)
        updateBoard(board)
    if role_server:
        role = role_server
    if sign_server:
        sign = sign_server
        const = 1 - signs.index(sign)
    if status_server:
        num = {1: "X", 2: "O"}
        res_txt = "\nResult: "
        game_fin = status_server
        winner = data_dict.get("winner")
        if winner == "draw":
            res_txt = res_txt + "Draw"
        else:
            res_txt = res_txt + "Winner " + num.get(winner)
        if game_fin:
            fin_lbl = ttk.Label(game_end, text="Game is over!" + res_txt, font=("Helvetica", 20))
            fin_lbl.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
            game_end.tkraise()
    if turn_server:
        turn = turn_server
    if turn_msg:
        msg = turn_msg
        turn_label.configure(text=msg)
    if conn_id:
        self_id = conn_id
    if sender_server:
        sender_id = sender_server
    if reaction_server:
        updateChat(reaction_server)
    can_process = 1


def process_input():
    while 1:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            data = data.decode("utf-8")
            data_dict = ast.literal_eval(data)
            client_thread = threading.Thread(
                target=handle, args=(data_dict,))
            client_thread.start()
        except ConnectionAbortedError:
            break
    return

can_process = 0
client_thread = threading.Thread(target=process_input)
client_thread.start()

def clicked(clicked_row, clicked_col):
    global can_process,turn, role,const, game_details, client_socket,b
    if can_process:
        if msg is not None and role == "player":
            
            if msg == "Your turn!" and not game_fin:
                game_details["move"] = str(clicked_row) + "$" + str(clicked_col)
                game_details["move_sign"] = sign
                client_socket.send(bytes(str(game_details), "utf-8"))

for i in range(3):
    for j in range(3):
                                          
        b[i][j] = Button(main_frame,
                        height = 4, width = 8,
                        font = ("Helvetica","20"),
                        command = lambda r = i, c = j : clicked(r,c))
        b[i][j].grid(row = i + 1, column = j)
 
 
mainloop()   