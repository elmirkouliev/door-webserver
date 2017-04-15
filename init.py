import json, requests, datetime
from flask import Flask, request

app = Flask(__name__)

# Networking
# 
ROOT = 'http://raspberrypi.local';
MOPIDY = ROOT + ":6680/mopidy/rpc"
PLAYLIST = "fresh"

# Sensors
DOOR = 'door'
MOTION = 'motion';
THRESHOLD = 5000;

sensors = {
    'door': {
        'state': 0,
        'updated_at': None
    },
    'motion' : {
        'state': 0,
        'updated_at': None
    }
}

def mopidyRequestBody(method, params):
    body = {
        "jsonrpc": "2.0", 
        "id": 1, 
        "method": method
    }

    if params is not None:
        body['params'] = params

    return body;

def handleSensor (sensor, state):
    """Handles sensor data and determines if we should start the playlist"""

    if sensors[sensor] is None:
        return

    # Check if it's the door
    if sensor == DOOR:

        # Has it just been opened
        if int(state) == 1:
            # Save to state
            sensors[sensor]['state'] = state;
            sensors[sensor]['updated_at'] = datetime.datetime.now();

        # Has it been closed?
        elif int(state) == 0:

            # Is it currently open?
            if int(sensors[sensor]['state']) == 1:
                print('Playing...');
                startPlaylist();

            sensors[sensor]['state'] = state;
            sensors[sensor]['updated_at'] = datetime.datetime.now();

    print(sensors);

def post (url, body):
    response = requests.post(url, json=body);

    if response.status_code > 200:
        raise ValueError('Can\'t make request to ' + url);

    return json.loads(response.text);


def startPlaylist(): 
    playlist = None
    playlists = post(MOPIDY, mopidyRequestBody("core.playlists.as_list", None));

    for result in playlists['result']:

        if(result['name'].lower() == PLAYLIST):
            playlist = result
            break

    clearTracks = post(MOPIDY, mopidyRequestBody("core.tracklist.clear", None))

    playList = {"uri" : playlist['uri']} 
    playPlaylist = post(MOPIDY, mopidyRequestBody('core.tracklist.add', playList))
    play = post(MOPIDY, mopidyRequestBody('core.playback.play', None))


@app.route('/sensor', methods=['GET'])
def sensor():
    sensor = request.args.get('sensor')
    state = request.args.get('state')

    if sensor is not None and state is not None:
        handleSensor(sensor, state)
        return 'ok';
    else:
        return 'Missing parameters!', 400

@app.errorhandler(404)
def page_not_found(error):
    return 'Not found!'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


