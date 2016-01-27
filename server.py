from flask import Flask, render_template, jsonify, session, request
import requests

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
    song = {'name': 'happy bday ' + player, 'author': 'Minnie Mouse'}

    return jsonify(song)



####################################
if __name__ == "__main__":
    app.run(debug=True)
