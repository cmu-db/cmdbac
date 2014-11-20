#!/usr/bin/env bash

if [ -n "$http_proxy" ]
then
    echo "export http_proxy=\"$http_proxy\"" >> /home/vagrant/.bashrc
    echo "export https_proxy=\"$http_proxy\"" >> /home/vagrant/.bashrc

    export http_proxy="$http_proxy"
    export https_proxy="$http_proxy"

    echo "Acquire::http::Proxy \"$http_proxy\";" > /etc/apt/apt.conf
fi

#update apt-get
apt-get update

##install sqlite3
#apt-get -y install sqlite3
#
##install mysql
#debconf-set-selections <<<'mysql-server mysql-server/root_password password your_password'
#debconf-set-selections <<<'mysql-server mysql-server/root_password_again password your_password'
#apt-get -y install mysql-server
#apt-get -y install libmysqlclient-dev
#apt-get -y install python-dev
#
##install postgresql
#apt-get -y install postgresql postgresql-contrib
#apt-get -y install libpq-dev


#apt-get -y install python-pip
wget https://bootstrap.pypa.io/get-pip.py -O /home/vagrant/get-pip.py
python /home/vagrant/get-pip.py

echo 'export PYTHONUSERBASE="/home/vagrant/pip"' >> /home/vagrant/.bashrc
