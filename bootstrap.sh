#!/usr/bin/env bash


#echo 'export http_proxy="http://proxy.pdl.cmu.edu:8080"' >> /home/vagrant/.bashrc
#echo 'export https_proxy="http://proxy.pdl.cmu.edu:8080"' >> /home/vagrant/.bashrc
echo 'export PYTHONUSERBASE="/home/vagrant/pip"' >> /home/vagrant/.bashrc

#export http_proxy="http://proxy.pdl.cmu.edu:8080"
#export https_proxy="http://proxy.pdl.cmu.edu:8080"

#echo 'Acquire::http::Proxy "http://proxy.pdl.cmu.edu:8080";' > /etc/apt/apt.conf

#update apt-get
apt-get update

#install sqlite3
apt-get -y install sqlite3

#install mysql
debconf-set-selections <<<'mysql-server mysql-server/root_password password your_password'
debconf-set-selections <<<'mysql-server mysql-server/root_password_again password your_password'
apt-get -y install mysql-server
apt-get -y install libmysqlclient-dev
apt-get -y install python-dev

#install postgresql
apt-get -y install postgresql postgresql-contrib
apt-get -y install libpq-dev

#apt-get -y install python-pip
