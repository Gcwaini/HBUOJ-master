#! /bin/bash

sudo apt install git gcc g++ make python-dev libxml2-dev libxslt1-dev zlib1g-dev ruby-sass gettext curl
wget -q --no-check-certificate -O- https://bootstrap.pypa.io/get-pip.py | sudo python
wget -O- https://deb.nodesource.com/setup_4.x | sudo -E bash -
sudo apt install nodejs
npm install -g pleeease-cli

pip install -r requirements.txt
source make_style.sh
python manage.py collectstatic
python manage.py compilemessages
python manage.py compilejsi18n

python manage.py migrate
python manage.py loaddata navbar
python manage.py loaddata language_small
python manage.py loaddata demo