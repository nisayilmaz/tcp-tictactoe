import pygame
import sys
import socket
import ast
import threading
HOST = "127.0.0.1"
PORT = 7777

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))


board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

pygame.init()

WIDTH = 600
HEIGHT = 600
LINE_WIDTH = 5
BOARD_ROWS = 3
BOARD_COLS = 3
SQUARE_SIZE = 200
CIRCLE_RADIUS = 60
CIRCLE_WIDTH = 15
CROSS_WIDTH = 25
SPACE = 55

BG_COLOR = (31, 31, 31)
LINE_COLOR = (23, 145, 135)
CIRCLE_COLOR = (239, 231, 200)
CROSS_COLOR = (66, 66, 66)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('TIC TAC TOE')
screen.fill(BG_COLOR)


def draw_lines():

    pygame.draw.line(screen, LINE_COLOR, (0, SQUARE_SIZE),
                     (WIDTH, SQUARE_SIZE), LINE_WIDTH)

    pygame.draw.line(screen, LINE_COLOR, (0, 2 * SQUARE_SIZE),
                     (WIDTH, 2 * SQUARE_SIZE), LINE_WIDTH)

    pygame.draw.line(screen, LINE_COLOR, (SQUARE_SIZE, 0),
                     (SQUARE_SIZE, HEIGHT), LINE_WIDTH)

    pygame.draw.line(screen, LINE_COLOR, (2 * SQUARE_SIZE, 0),
                     (2 * SQUARE_SIZE, HEIGHT), LINE_WIDTH)


def draw_figures():
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 2:
                pygame.draw.circle(screen, CIRCLE_COLOR, (int(col * SQUARE_SIZE + SQUARE_SIZE//2), int(
                    row * SQUARE_SIZE + SQUARE_SIZE//2)), CIRCLE_RADIUS, CIRCLE_WIDTH)
            elif board[row][col] == 1:
                pygame.draw.line(screen, CROSS_COLOR, (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE -
                                 SPACE), (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SPACE), CROSS_WIDTH)
                pygame.draw.line(screen, CROSS_COLOR, (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE),
                                 (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE), CROSS_WIDTH)


def mark_square(row, col, player):
    board[row][col] = player


def available_square(row, col):
    return board[row][col] == 0


def is_board_full():
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 0:
                return False

    return True


program_fin = 0
role = ""
sign = ""
turn = 0
const = 1
game_details = {"move": "", "turn": 0, "result": ""}
signs = ["X", "O"]
game_fin = 0


def handle(data_dict, client_socket):
    global role, sign, turn, const, game_details, signs, game_fin, board, can_process
    can_process = 0
    turn = data_dict.get("turn", None)
    role_server = data_dict.get("role", None)
    move = data_dict.get("move", None)
    sign_server = data_dict.get("sign", None)

    if role_server:
        role = role_server
    if sign_server:
        sign = sign_server
        const = 1 - signs.index(sign)
    if move:
        x = int(move.split("$")[0])
        y = int(move.split("$")[1])
        opponent_sign = signs.index(data_dict.get("move_sign")) + 1
        board[x][y] = opponent_sign
        draw_figures()
    can_process = 1


def process_input():
    global program_fin
    while not program_fin:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            data = data.decode("utf-8")
            data_dict = ast.literal_eval(data)
            client_thread = threading.Thread(
                target=handle, args=(data_dict, client_socket,))
            client_thread.start()

        except ConnectionAbortedError:
            break
    return

can_process = 0
game_over = False
client_thread = threading.Thread(target=process_input)
client_thread.start()
draw_lines()
while True:
    if can_process:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                program_fin = 1
                client_socket.close()

                client_thread.join()
                sys.exit()
            player = signs.index(sign) + 1

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if turn is not None and role == "player":
                    turn = int(turn)
                    if turn % 2 == const and not game_fin:
                        mouseX = event.pos[0]
                        mouseY = event.pos[1]

                        clicked_row = int(mouseY // SQUARE_SIZE)
                        clicked_col = int(mouseX // SQUARE_SIZE)

                        if available_square(clicked_row, clicked_col):
                            mark_square(clicked_row, clicked_col, player)                        
                            draw_figures()

                        turn = turn + 1
                        game_details["move"] = str(clicked_row) + "$" + str(clicked_col)
                        game_details["move_sign"] = sign
                        game_details["turn"] = turn
                        client_socket.send(bytes(str(game_details), "utf-8"))

    pygame.display.update()
