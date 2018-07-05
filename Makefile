SHELL:=/bin/bash

help:
	@echo
	@echo "  Welcome."
	@echo
	@echo "    Target            Description"
	@echo "    -------------------------------------------------------------------"
	@echo "    clean             Cleanup installation"
	@echo "    help              You're reading this"
	@echo "    install           Clean, install set up project"
	@echo "    update            Clean, set up project"
	@echo
	@echo "  Have fun!"
	@echo

pyclean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf ./*.egg
	rm -rf ./*.egg-info

clean: pyclean

install_packages:
	apt update
	apt install -y \
		zlib1g-dev \
		libjpeg-dev \
		python3 \
		python3-dev \
		python3-setuptools \
		python3-pip \
		python3-yaml \
		python3-requests \
		python3-click \
		python3-mock \
		python3-aiohttp \
		python3-magic \
		python3-wand \
		python3-pypdf2 \
		libreoffice \
		inkscape
	rm -f /usr/bin/python
	ln -s /usr/bin/python3 /usr/bin/python
	rm -f /usr/bin/pip
	ln -s /usr/bin/pip3 /usr/bin/pip

systemctl_install:
	id -u previewgenerator &>/dev/null || useradd -m -r previewgenerator
	cp ./resources/previewgenerator-webserver.service /lib/systemd/system/previewgenerator-webserver.service
	cp ./resources/previewgenerator.service /lib/systemd/system/previewgenerator.service
	systemctl daemon-reload
	systemctl enable previewgenerator-webserver
	systemctl enable previewgenerator

install_project:
	python3 ./setup.py develop

update: clean
	git pull origin master
	python3 ./setup.py develop

install: clean install_packages install_project systemctl_install
