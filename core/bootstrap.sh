#!/usr/bin/env bash


# install the package that sometime needed for deploying django or ruby on rails apps
# continue adding packages to this file if missing some packages may cause common errors

# use this line if the host is using proxy, and change the proxy
# http_proxy=http://proxy.pdl.cmu.edu:8080

if [ -n "$http_proxy" ]
then
    echo "use proxy: "$http_proxy
    echo "export http_proxy=\"$http_proxy\"" >> /home/vagrant/.bashrc
    echo "export https_proxy=\"$http_proxy\"" >> /home/vagrant/.bashrc

    export http_proxy="$http_proxy"
    export https_proxy="$http_proxy"

    echo "Acquire::http::Proxy \"$http_proxy\";" > /etc/apt/apt.conf
else
    echo "not use proxy"
fi


#update apt-get
apt-get update

# install and configure git
apt-get -y install git

# install make

apt-get -y install make

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
wget https://bootstrap.pypa.io/get-pip.py -O /home/vagrant/get-pip.py
python /home/vagrant/get-pip.py

echo 'export PYTHONUSERBASE="/home/vagrant/pip"' >> /home/vagrant/.bashrc

# for ruby on rails

# can not find sqlite3.h
apt-get -y install libsqlite3-dev

apt-get -y install ruby-dev

# missing libxml2
apt-get -y install libxslt-dev libxml2-dev
# rake aborted! Could not find a JavaScript runtime
apt-get -y install nodejs 
# Can't find Magick-config
apt-get -y install libmagickwand-dev

# update ruby
apt-get -y install make
cd /vagrant/ruby-2.1.5
./configure
make
make install

gem update --system

gem install bundle

#echo 'export DATABASE_URL="sqlite3:/db/db_webcrawler.sqlite3"' >> /home/vagrant/.bashrc

apt-get -y install vim

#apt-get -y install curl
#git config --global user.name "Fangyu Gao"
#git config --global user.email "fangyugao1219@gmail.com"
#apt-get -y install ruby-rvm
#rvm get head
