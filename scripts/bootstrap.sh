#!/usr/bin/env bash

#update apt-get
sudo apt-get update

#install mysql
sudo debconf-set-selections <<<'mysql-server mysql-server/root_password password your_password'
sudo debconf-set-selections <<<'mysql-server mysql-server/root_password_again password your_password'
sudo apt-get -y install mysql-server
sudo apt-get -y install libmysqlclient-dev
sudo apt-get -y install python-dev

#install postgresql
sudo apt-get -y install postgresql postgresql-contrib
sudo apt-get -y install libpq-dev

sudo apt-get -y install python-pip
