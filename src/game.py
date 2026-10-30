from os import name, system
from random import randint

from algos.Random import RandomStrategy
from algos.minimax_strategy import MinimaxStrategy
from connect_four import COLUMNS, PLAYER_ONE, PLAYER_TWO, GameState


HUMAN_PLAYER = PLAYER_TWO
AI_PLAYER = PLAYER_ONE
game_mode = "minimax"


def clear_terminal():
    system("clear" if name == "posix" else "cls")


def print_board(state: GameState):
    clear_terminal()
    print("*************************************")
    print("")
    for row in range(5, -1, -1):
        print("      |", end="")
        for column in range(COLUMNS):
            print(f"{state.board[row][column]:2}|", end="")
        print("\n")
    print("      |1 |2 |3 |4 |5 |6 |7 |")


def main():
    print("*************************************")
    print("Welcome to the game connect four!")
    print("*************************************")

    state = GameState.initial()
    strategy = (
        RandomStrategy()
        if game_mode == "random"
        else MinimaxStrategy(depth=4)
    )
    print_board(state)

    if randint(0, 1) == 1:
        state = GameState(state.board, HUMAN_PLAYER)

    while not state.is_terminal():
        if state.current_player == HUMAN_PLAYER:
            print("*************************************")
            print("Player HUMAN has to make the next move!")
            chosen_column = int(input("\nInput a number from 1-7 for column\n")) - 1
        else:
            print("*************************************")
            print("Player AI has to make the next move!")
            chosen_column = strategy.choose_move(state)
            print(f"AI chooses column {chosen_column + 1}")

        if chosen_column not in state.legal_moves():
            print("That column is not available.")
            continue

        state = state.drop_piece(chosen_column)
        print_board(state)

    winner = state.winner()
    if winner == HUMAN_PLAYER:
        print("WIN HUMAN")
    elif winner == AI_PLAYER:
        print("WIN AI")
    else:
        print("DRAW")


if __name__ == "__main__":
    main()
