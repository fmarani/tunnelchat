import 'package:angular/angular.dart';
import 'dart:html';
import 'dart:convert';


// Temporary, please follow https://github.com/angular/angular.dart/issues/476
@MirrorsUsed(override: '*')
import 'dart:mirrors';

WebSocket ws;

void main() {
  ws = new WebSocket("ws://localhost:8888/chatsocket");
  InputElement uploadInput = querySelector('#file');
    uploadInput.onChange.listen((e) {
      // read file content as dataURL
      final files = uploadInput.files;
      if (files.length == 1) {
        final file = files[0];
        final reader = new FileReader();
        reader.onLoad.listen((e) {
          sendFile(file.name, reader.result);
        });
        reader.readAsDataUrl(file);
      }
    });
  ngBootstrap(module: new ChatModule());
}

sendFile(String file, dynamic data) {
  final req = new HttpRequest();
  req.onReadyStateChange.listen((Event e) {
    if (req.readyState == HttpRequest.DONE &&
        (req.status == 200 || req.status == 0)) {
      window.alert("upload complete");
    }
  });
  req.open("POST", "/upload");
  req.send(JSON.encode({"filename": file, "data": data}));
}

class ChatModule extends Module {
  ChatModule() {
    type(MainController);
    type(EnterSubmit);
  }
}

@NgController(
    selector: '[chat-app]',
    publishAs: 'ctrl')
class MainController {
  Http _http;
  List messages;
  List users;
  Message selectedMessage;
  String in_progress_msg;
  
  MainController(this._http) {
    messages = [];
    users = [];
    ws.onOpen.listen((e) {
      updateUserList();  
    });
    ws.onMessage.listen((MessageEvent e) {
        var event = JSON.decode(e.data);
        var msg = new Message(event['when'], event['from'], event['body']);
        messages.add(msg);
        updateUserList();
        querySelector("#inbox").scrollByLines(1);
        
    });
    adjustBoxSizes();
    window.onResize.listen((e) {
      adjustBoxSizes();
    });
        
    
    
  }
  
  void adjustBoxSizes() {
        var height = window.innerHeight - 60;
        querySelector('#inbox').style.height = "${height}px";
        querySelector('#userlist').style.height = "${height}px";
        var width = window.innerWidth - 130;
        querySelector('#inbox').style.width = "${width}px";
  }
  
  void selectMessage(Message msg) {
    selectedMessage = msg;
    
  }
  
  void addMessage() {
    ws.send(in_progress_msg);
    in_progress_msg = "";

  }
  
  void updateUserList() {
    users = [];
    _http.get("/userlist")
      .then((HttpResponse response) {
        for (String username in response.data['users']) {
          var me = false;
          if (response.data['current_user'] == username) {
            me = true;
          }
          users.add(new User(username, me));
        }              
      });
  }
}

@NgDirective(
  selector: '[ng-enter-submit]')
class EnterSubmit {
  Element element;

  @NgCallback("submit")
  Function submit;
  
  EnterSubmit(this.element) {
  element.onKeyPress.listen((event) {
    if(event.which == 13 && !event.shiftKey) {
      submit();
      event.preventDefault();
    }
  });
  }
}

class Message {
  String when;
  String from;
  String body;
  
  Message(this.when, this.from, this.body); 
}

class User {
  String name;
  bool me;
  User(this.name, this.me);
  
  css() {
    if (me) {
      return ["me"];
    } else {
      return ["other"];
    }
  }
}
