css:
	compass compile

watch:
	compass watch

main.dart.js: main.dart
	dart2js -o main.dart.js main.dart

dart: main.dart.js

all: css dart

.PHONY: css watch
