static/main.dart.js: static/main.dart
	dart2js -o static/main.dart.js static/main.dart

all: static/main.dart.js
