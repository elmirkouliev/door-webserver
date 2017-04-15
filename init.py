from flask import Flask, request

app = Flask(__name__)

@app.route('/sensor', methods=['GET'])
def door():
    open = request.args.get('door')

    if open is not None:
        print(open);
    else:
        return 'Missing parameters!', 400


@app.errorhandler(404)
def page_not_found(error):
    return 'Not found!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')