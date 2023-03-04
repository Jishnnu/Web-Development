import os

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import requests

application = Flask(__name__)
application.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(application)

channel_list = ["lobby"]
online_list = []
messages = {"lobby": []}


@application.route("/")
def index():
    return redirect(url_for('channel', name='lobby'))


@application.route("/c/<string:name>")
def channel(name):
    if name not in channel_list:
        return "The channel {} does not exist.".format(name)

    return render_template("channel.html", online_list=online_list, channel_list=channel_list, messages=messages[name], current_channel=name)


@application.route('/request_online', methods=['GET', 'POST'])
def request_online():
    duplicate = False

    if request.json['data'] in online_list:
        duplicate = True

    return jsonify({"duplicate": duplicate})


@application.route('/request_channels', methods=['GET', 'POST'])
def request_channels():
    duplicate = False

    if request.json['data'] in channel_list:
        duplicate = True

    return jsonify({"duplicate": duplicate})


@socketio.on("add message")
def sent(data):
    print("message received")
    messages[data["channel"]].append(
        (data["user"], data["time"], data["message"]))

    while(len(messages[data["channel"]]) > 100):
        messages[data["channel"]].pop(0)

    emit("announce message", {"user": data["user"], "time": data["time"],
         "message": data["message"], "channel": data["channel"]}, broadcast=True)


@socketio.on("add user")
def joined(data):
    if data['display'] not in online_list:
        print(str(data['display']) + " has joined!")
        online_list.append(data['display'])
        emit("announce online", {"online": len(
            online_list), "display": data['display'], "event": "add"}, broadcast=True)
    print(data['display'] + " is already logged in!")


@socketio.on("remove user")
def gone(data):
    print(data['display'] + " has left!")
    online_list.remove(data['display'])
    emit("announce online", {"online": len(
        online_list), "display": data['display'], "event": "remove"}, broadcast=True)


@socketio.on("add channel")
def add_channel(data):
    print(data['channel'] + " has been added to channel list!")
    channel_list.append(data['channel'])
    messages.setdefault(data['channel'], [])
    emit("announce channel", {"channel": data['channel']}, broadcast=True)


if __name__ == "__main__":
    application.run()
