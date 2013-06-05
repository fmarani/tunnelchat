// Copyright 2009 FriendFeed
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

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
    updater.start();
});

function newMessage() {
    var message = $("#message");
    updater.socket.send(message.val());
    message.val("").select();
}


function notify(from, msg) {
    if (window.webkitNotifications) {
        var havePermission = window.webkitNotifications.checkPermission();
        if (havePermission == 0) {
            // 0 is PERMISSION_ALLOWED
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

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/chatsocket";
	updater.socket = new WebSocket(url);
	updater.socket.onmessage = function(event) {
	    updater.showMessage(JSON.parse(event.data));
	}
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html);
        notify(message.from, message.body);
        $("#inbox").append(node);
        $("#inbox").scrollTop($("#inbox")[0].scrollHeight);
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
   // var message = "New file uploaded - " + evt.target.responseText;
   // updater.socket.send(message);
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
