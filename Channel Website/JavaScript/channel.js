var current_channel = document.URL.split("/").pop();

// Connect to websocket
//var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
var socket = io.connect();

// when user exits out, emit user has left to server
window.onbeforeunload = () => {
    socket.emit('remove user', {
        'display': localStorage.getItem('display')
    });
}

// When the webpage is done loading ...
document.addEventListener('DOMContentLoaded', () => {
    // Add onclick event listener to create channel button
    document.getElementById("new-channel-button").addEventListener("click", () => {

        // prompt for a channel name
        let channel_name = prompt("Enter a channel name")
        socket.emit('add channel', {
            'channel': channel_name
        })
    });

    // When client is connected ...
    socket.on('connect', () => {
        // Prompt for display name if not set
        if (localStorage.getItem('display') == null) {
            var display = prompt("Enter a display name: ")

            localStorage.setItem('display', display);
        }

        // update display name label
        document.querySelector("span#display_label").innerHTML = localStorage.getItem('display');

        // update online list on server with the new user
        socket.emit('add user', {
            "display": localStorage.getItem("display")
        });

        // when user presses send button, emit the message to server.
        document.getElementById("send-button").onclick = () => {
            console.log('enter pressed');
            let text = document.querySelector('input');
            let time = new Date();

            // send message to server
            socket.emit('add message', {
                'user': localStorage.getItem('display'),
                'time': time.toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true }),
                'message': text.value,
                'channel': current_channel
            });

            //clear input box
            text.value = "";
        }

        // when user presses enter in input box, fire onclick event
        document.getElementById("message-input").onkeyup = event => {
            if (event.keyCode == 13) {
                document.getElementById("send-button").click();
            }
        };

    });


    // When a message is announce, add the message to specific channel
    socket.on("announce message", data => {

        // only add message to the specifed channel
        if (data["channel"] == current_channel) {

            let messageblock = `<article class="message">
                    <span class="user">${data["user"]}</span> <span class="time">[${data["time"]}]</span>
                    <p>${data["message"]}</p>
                    </article>`;

            document.querySelector('#messages-container').innerHTML += messageblock;

            // scroll to the bottom of chatbox
            var nodes = document.querySelectorAll('article');
            nodes[nodes.length - 1].scrollIntoView(true);
        }
    });


    //When a change to online count is announced
    socket.on('announce online', data => {
        document.querySelector('#online_count').innerHTML = data["online"];

        // if user joined, add them onto online list
        if (data["event"] == "add") {
            let new_user = `<tr><td>${data['display']}</td></tr>`;
            document.getElementById("online_table").innerHTML += new_user;
        }

        // if user left, remove them from online list
        else if (data["event"] == "remove") {
            var list = document.getElementById("online_table");
            for (i = 0; i <= list.childNodes.length; i++) {
                if (list.childNodes[i].childNodes[0] != undefined) {
                    if (list.childNodes[i].childNodes[0].innerHTML == data['display']) {
                        list.removeChild(list.childNodes[i]);
                        return;
                    }
                }
            }
        }
    });

    //When a new channel is announced, update channel list
    socket.on('announce channel', data => {
        console.log('new channel announced');
        let link = "/c/" + data['channel'];
        let new_channel = `<tr><td># <a href="${link}">${data['channel']}</a></td></tr>`;
        document.getElementById("channel_table").innerHTML += new_channel;
    });
});