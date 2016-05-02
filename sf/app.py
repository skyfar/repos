import sflib
import sfm

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)
app.debug = True

init_pos = sfm.parseFEN(sfm.FEN_INITIAL)
curr_pos = init_pos
@app.route("/", methods=['GET', 'POST'])
def nextmove():
    global curr_pos
    error = None
    mymove = None
    if curr_pos == init_pos:
        white_move = sfm.next_move(curr_pos)
        mymove = sflib.format_move(white_move)
        curr_pos = curr_pos.move(white_move)
    if request.method == 'POST':
        black_move = sfm.accept_move(curr_pos, request.form['yourmove'])
        if not black_move:
            error = 'Invalid move'
        else:
            curr_pos = curr_pos.move(black_move)
            white_move = sfm.next_move(curr_pos)
            mymove = sflib.format_move(white_move)
            curr_pos = curr_pos.move(white_move)
    board = curr_pos.rotate().board
    return render_template('index.html', board = board, mymove = mymove, error = error)

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0')
    except:
        raise
    finally:
        sfm.clean_up()

