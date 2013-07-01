
$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#messageform").on("submit", function() {
        newMessage();
        if (window.webkitNotifications) {
            window.webkitNotifications.requestPermission();
        }
        return false;
    });
    $("#messageform").on("keypress", function(e) {
        if (e.keyCode == 13 && !e.shiftKey) {
            newMessage();
            if (window.webkitNotifications) {
                window.webkitNotifications.requestPermission();
            }
            return false;
        }
    });
    $("#message").select();
    chat.start();
});

function newMessage() {
    var message = $("#message");
    chat.socket.send(message.val());
    message.val("").select();
}


function notify(from, msg) {
    if (window.webkitNotifications) {
        var havePermission = window.webkitNotifications.checkPermission();
        if (havePermission == 0) {
            // 0 is PERMISSION_ALLOWED
            if (msg.search("@" + chat.current_user) >= 0) {
                var notification = window.webkitNotifications.createNotification(
                'http://i.stack.imgur.com/dmHl0.png',
                from,
                msg
                );
                
                notification.show();
                setTimeout(function() {
                    notification.cancel();
                }, '5000');
            }
        } 
    }
}  

function updateUserList() {
    function refreshList(result) {
        responseJson = JSON.parse(result.target.response);
        $("#userlist")[0].innerText = responseJson.users;
        chat.users = responseJson.users;
        chat.current_user = responseJson.current_user;
    }
  var xhr = new XMLHttpRequest();

  /* event listners */
  xhr.addEventListener("load", refreshList, false);
  xhr.open("GET", "/userlist");
  xhr.send();
}
    

var chat = {
    socket: null,
    users: [],
    current_user: null,

    start: function() {
        var url = "ws://" + location.host + "/chatsocket";
	chat.socket = new WebSocket(url);
	chat.socket.onmessage = function(event) {
	    chat.showMessage(JSON.parse(event.data));
	}
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html);
        notify(message.from, message.body);
        $("#inbox").append(node);
        $("#inbox").scrollTop($("#inbox")[0].scrollHeight);
        if (message.system == true) {
            updateUserList();
        }
    }
};

function uploadProgress(evt) {
    if (evt.lengthComputable) {
      var percentComplete = Math.round(evt.loaded * 100 / evt.total);
      document.getElementById('progressNumber').innerHTML = percentComplete.toString() + '%';
    }
    else {
      document.getElementById('progressNumber').innerHTML = 'unable to compute';
    }
  }

  function uploadComplete(evt) {
  }

  function uploadFailed(evt) {
    alert("There was an error attempting to upload the file." + evt);
  }

  function uploadCanceled(evt) {
    alert("The upload has been canceled by the user or the browser dropped the connection.");
  }

function uploadFile() {
  var xhr = new XMLHttpRequest();
  var fd = new FormData(document.getElementById('form1'));

  /* event listners */
  xhr.upload.addEventListener("progress", uploadProgress, false);
  xhr.addEventListener("load", uploadComplete, false);
  xhr.addEventListener("error", uploadFailed, false);
  xhr.addEventListener("abort", uploadCanceled, false);
  xhr.open("POST", "/upload");
  xhr.send(fd);
  return false;
}
$("#form1").submit(uploadFile);
