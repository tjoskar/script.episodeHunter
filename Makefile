all: zip

zip:
	zip -r script.episodehunter.zip . \
		-x '.venv*' \
		-x '.vscode*' \
		-x '*.git*' \
		-x 'test*' \
		-x '.pylintrc' \
		-x 'Makefile' \
		-x '*.DS_Store*' \
		-x '*__pycache__*' \
		-x '*.pyc*' 
