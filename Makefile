all: zip

zip:
	cd ../ && zip -r script.episodeHunter.zip script.episodeHunter -x '*.git*' -x '*.venv*' -x '*.DS_Store*' -x '*__pycache__*' -x '*.pyc*' -x '*.vscode*' -x '*test*' && mv script.episodeHunter.zip script.episodeHunter
