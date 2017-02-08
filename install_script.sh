#!/bin/bash

sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install python python-pip python-tk -y
pip install --upgrade pip
git clone https://github.com/nateGeorge/udacity_review_assigner.git
cd grading-assigner
pip install -r requirements.txt

# from here: https://docs.mongodb.com/v3.0/tutorial/install-mongodb-on-ubuntu/
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list
sudo apt-get update
sudo apt-get install mongodb-org -y
# need to enter something into this file:
# sudo nano /etc/systemd/system/mongodb.service
# from here: http://askubuntu.com/questions/770054/mongodb-3-2-doesnt-start-on-lubuntu-16-04-lts-as-a-service
# then do:
# sudo systemctl start mongodb
# sudo systemctl enable mongodb
