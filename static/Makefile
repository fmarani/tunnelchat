clean:
	rm -fr css main.dart.js main.dart.js.map main.dart.js.deps

css:
	compass compile

watch:
	compass watch

main.dart.js: main.dart
	dart2js -o main.dart.js main.dart

dart: main.dart.js

all: css dart

.PHONY: css watch
