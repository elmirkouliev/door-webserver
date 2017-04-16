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
MIN_OPEN_TIME = 3;
MAX_OPEN_TIME = 13;

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
            updateState(sensor, state);

        # Has it been closed?
        elif int(state) == 0:

            # Is it currently open?
            if int(sensors[sensor]['state']) == 1:
                diff = datetime.datetime.now() - sensors[sensor]['updated_at'];

                print(diff.seconds);

                # Has it open enough
                if diff.seconds >= MIN_OPEN_TIME and diff.seconds < MAX_OPEN_TIME:
                    print('Playing...');
                    updateState(sensor, state);
                    startPlaylist();
                else:
                    print('Stopping...');
                    updateState(sensor, state);
                    stop();
            else:
                updateState(sensor, state);

    return "{ \"sensor\" : " + sensor + ", \"state\" : " + state + " }";

def updateState (sensor, state):
    sensors[sensor]['state'] = state;
    sensors[sensor]['updated_at'] = datetime.datetime.now();                    

def post (url, body):
    response = requests.post(url, json=body);

    if response.status_code > 200:
        raise ValueError('Can\'t make request to ' + url);

    return json.loads(response.text);

def startPlaylist(): 
    status = post(MOPIDY, mopidyRequestBody("core.playback.get_state", None))

    # Check if music is already playing
    if status['result'] == "playing":
        print("Already playing")
        return

    # Fetch current tracks in queue
    currentTracks = post(MOPIDY, mopidyRequestBody("core.tracklist.get_tracks", None))
    # Fetch playlists
    playlists = post(MOPIDY, mopidyRequestBody("core.playlists.as_list", None));

    # Find the one we're looking for
    for result in playlists['result']:
        if(result['name'].lower() == PLAYLIST):
            playlist = result
            break

    if playlist is None:
        print("Can\'t find playlist: ", PLAYLIST)
        return

    playListItems = post(MOPIDY, mopidyRequestBody("core.playlists.get_items", {"uri" : playlist['uri']}))

    similar = 0;

    # Count the number of similar tracks in current tracklist and the playlist
    for track in playListItems['result']:
        if len(
            filter(lambda currTrack: track['uri'] in currTrack['uri'], currentTracks['result'])
        ) > 0:
            similar += 1;

    post(MOPIDY, mopidyRequestBody("core.playlists.refresh", {"uri" : playlist['uri']}))

    # Playlist isn't currently playing
    if similar < 4:
        post(MOPIDY, mopidyRequestBody("core.tracklist.clear", None))
        post(MOPIDY, mopidyRequestBody('core.tracklist.add', {"uri" : playlist['uri']}))
        post(MOPIDY, mopidyRequestBody('core.tracklist.shuffle', None))
    else:
        post(MOPIDY, mopidyRequestBody('core.playback.play', None))

def stop():
    stop = post(MOPIDY, mopidyRequestBody('core.playback.stop', None))

@app.route('/sensor', methods=['GET'])
def sensor():
    sensor = request.args.get('sensor')
    state = request.args.get('state')

    if sensor is not None and state is not None:
        return handleSensor(sensor, state)
    else:
        return 'Missing parameters!', 400

@app.errorhandler(404)
def page_not_found(error):
    return 'Not found!'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


