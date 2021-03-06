#!/usr/bin/env pypy
# -*- coding: utf-8 -*-

from __future__ import print_function
from multiprocessing import Process, Queue
import sys, re, random, time, argparse

import sflib

# Python 2 compatability
if sys.version_info[0] == 2:
    input = raw_input

in_q = Queue()
out_q = Queue()
def work(in_q, out_q, depth):
    while True:
        move, pos = in_q.get()
        out_q.put((move, sflib.search(pos, depth)))

worker_list = []
def init(workers, depth):
    for i in range(workers):
        worker_list.append(Process(target=work, args=(in_q, out_q, depth,)))
        worker_list[i].start()
    
def clean_up():
    for w in worker_list:
        w.terminate()

#WHITE, BLACK = range(2)
FEN_INITIAL = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

def parseFEN(fen):
    """ Parses a string in Forsyth-Edwards Notation into a Position """
    board, color, castling, enpas, _hclock, _fclock = fen.split()
    board = re.sub(r'\d', (lambda m: '.'*int(m.group(0))), board)
    board = ' '*19+'\n ' + '\n '.join(board.split('/')) + ' \n'+' '*19
    wc = ('Q' in castling, 'K' in castling)
    bc = ('k' in castling, 'q' in castling)
    ep = sflib.parse(enpas) if enpas != '-' else 0
    score = sum(sflib.pst[p][i] for i,p in enumerate(board) if p.isupper())
    score -= sum(sflib.pst[p.upper()][i] for i,p in enumerate(board) if p.islower())
    pos = sflib.Position(board, score, wc, bc, ep, 0)
    return pos if color == 'w' else pos.rotate() 

def init_board(board_file):
    with open(board_file) as f:
        return parseFEN(f.read())

def weighted_choice(wlist):
    rnd = random.random() * sum(wlist)
    for i, w in enumerate(wlist):
        rnd -= w
        if rnd < 0:
            return i

opening_list = {}
def init_openings():
    global opening_list
    pos = parseFEN(FEN_INITIAL)
    opening_list[pos] = ([sflib.unformat_move(m) for m in ('e2e4', 'd2d4', 'b1c3', 'g1f3', 'c2c4')], (10, 10, 6, 6, 4))
init_openings()

def next_move(pos):
    t = time.time()
    opening_moves = opening_list.get(pos)
    if opening_moves:
        return opening_moves[0][weighted_choice(opening_moves[1])]

    valid_moves = pos.valid_moves()
    for move in valid_moves:
        next_pos = pos.move(move)
        in_q.put((move, next_pos))

    next_moves = []
    for i in range(len(valid_moves)):
        (move, (next_move, score, depth)) = out_q.get()
        if next_move:
            next_moves.append((move, next_move, score, depth))
        else:
            print('failed to search for move: ', sflib.format_move(move))

    if not next_moves:
        print('no solution for', pos.board)
        return None

    best_move = min(next_moves, key=lambda m: m[2])
    if best_move[2] < 0 - sflib.MATE_VALUE:
        print('You will lose...')
        return min([m for m in next_moves if m[2] < 0-sflib.MATE_VALUE], key=lambda m: m[3])[0]

    candidate_moves = sorted([move for move in next_moves if abs(move[2] - best_move[2]) < 51], key=lambda m: m[2])
    weight_list = []
    for move in candidate_moves:
        # priority: 0-0, P/N/B in initial position
        s_from = move[0][0]
        s_to = move[0][1]
        piece = pos.board[s_from]
        if move[0] == (95, 97):
            weight = 100
        elif move[0] == (95, 93):
            weight = 80
        elif s_from in (84, 85) and piece == 'P':
            if s_to in (64, 65):
                weight = 40
            else:
                weight = 10
        elif s_from == 97 and piece == 'N':
            if s_to == 76:
                weight = 30
            elif s_to == 85:
                weight = 10
        elif s_from == 92 and piece == 'N':
            if s_to == 73:
                weight = 25
            elif s_to == 84:
                weight = 8
        elif s_from == 96 and piece == 'B':
            weight = 28
        elif s_from == 93 and piece == 'B':
            weight = 18
        elif s_from == 88 and s_to == 78 and piece == 'P' and pos.board[85] == 'P' \
                and pos.board[95] == 'K' and pos.board[96] == 'B':
            weight = 8
        else:
            weight = 1
        weight_list.append(weight)
        #print('move: ' + piece + sflib.format_move(move[0]) + ', score:',  str(move[2]) + ', depth:', str(move[3]), ', weight:', weight)
    print('think time=', time.time() -t, end='\t')
    return candidate_moves[weighted_choice(weight_list)][0]

def rotate_move(move):
    return (119-move[0], 119-move[1])

def accept_move(pos, str_move):
    match = re.match('([a-h][1-8])'*2, str_move)
    if match:
        move = rotate_move((sflib.parse(match.group(1)), sflib.parse(match.group(2))))
        if move in pos.valid_moves():
            return move
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', type=int, default=4)
    parser.add_argument('-w', type=int, default=4)
    parser.add_argument('-r', action='store_true')
    parser.add_argument('-m', action='store_true')
    parser.add_argument('-i', type=file)
    args = parser.parse_args()

    try:
        if args.r:
            rec_f = open(time.strftime('rec-%Y%m%d-%H%M%S.txt'), 'w')
        if args.i is not None:
            pos = parseFEN(args.i.read())
            if args.r: rec_f.write(pos.board+'\n')
        else:
            pos = parseFEN(FEN_INITIAL)

        init(args.w, args.d)
        step = 0
        while True:
            step += 1
            #sflib.print_pos(pos)
            white_move = next_move(pos)
            if not white_move:
                break
            print(str(step), 'Wmove:', sflib.format_move(white_move))
            pos = pos.move(white_move)

            #sflib.print_pos(pos.rotate())
            if args.m:
                #machine vs. machine
                time.sleep(1)
                black_move = next_move(pos)
                print('Bmove:', sflib.format_move(black_move, True))
            else:
                black_move = None
                while not black_move:
                    black_move = accept_move(pos, input('Your move:'))
            if args.r:
                rec_f.write(str(step)+'. ' + sflib.format_move(white_move) \
                        + ', ' + sflib.format_move(black_move, True) + '\n')
                rec_f.flush()
            pos=pos.move(black_move)
    except BaseException as e:
        print(e)
    finally:
        if args.r:
            rec_f.close()
        clean_up()

    return

if __name__ == '__main__':
    main()
