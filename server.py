from flask import Flask, render_template, jsonify, session, request
import requests
import os
import re

app = Flask(__name__)
app.secret_key = "ABC"

####################################


@app.route('/')
def index():

    return render_template('index.html')


@app.route('/greet', methods=['GET'])
def greet():
    user = request.args.get("person")
    topic = request.args.get("subject")
    session['user'] = user

    payload = {'term': topic}
    r = requests.get('https://itunes.apple.com/search', params=payload)

    jdict = r.json()
    num_songs = jdict['resultCount']
    jlist = jdict['results']

    return render_template('greeting.html', player=user, subj=topic,
                           songs=jlist, total_num=num_songs)


@app.route('/song.json')
def getSong():
    player = session['user']
    song_file = open("song.txt")
    lyrics = []
    song = {'Title': 'Hey There ' + player,
            'Artist': 'Plain Robot T\'s',
            'Lyrics': lyrics,
            }

    count = 0
    for line in song_file:
        count += 1
        line = line.strip()
        if line == "":
            new_line = "*" * 20
        else:
            new_line = re.sub("Delilah", player, line)
        lyrics.append(new_line)

    return jsonify(song)



####################################
if __name__ == "__main__":
    DEBUG = "NO_DEBUG" not in os.environ
    PORT = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
