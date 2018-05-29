#!/bin/bash
#
# Prepare system for Web Dashboard Flask
#

read -p "User Proxy: " user
read -p "Password Proxy: " pass

export http_proxy="http://$user:$pass@cache.itb.ac.id:8080"
export https_proxy="http://$user:$pass@cache.itb.ac.id:8080"

echo "Install python-pip package"
sudo apt-get install python-pip

echo "Install Flask-WTF module"
sudo -E pip install flask-wtf

echo "Install Flask-CORS module"
sudo -E pip install flask-cors

echo " System Ready "
