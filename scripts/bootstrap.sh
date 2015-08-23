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


# update apt-get
apt-get update

# install essentials
apt-get -y install git
apt-get -y install make
apt-get -y install sqlite3
apt-get -y install python-dev
apt-get -y install unzip

# install pip
wget https://bootstrap.pypa.io/get-pip.py -O /home/vagrant/get-pip.py
python /home/vagrant/get-pip.py
echo 'export PYTHONUSERBASE="/home/vagrant/pip"' >> /home/vagrant/.bashrc

# install mysql
debconf-set-selections <<<'mysql-server mysql-server/root_password password your_password'
debconf-set-selections <<<'mysql-server mysql-server/root_password_again password your_password'
apt-get -y install mysql-server
apt-get -y install libmysqlclient-dev
pip install MySQL-python

# install postgresql
apt-get -y install postgresql postgresql-contrib
apt-get -y install libpq-dev

# install beautifulsoup
pip install BeautifulSoup4

# install django
pip install django

# install ruby
cd
git clone git://github.com/sstephenson/rbenv.git .rbenv
echo 'export PATH="$HOME/.rbenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(rbenv init -)"' >> ~/.bashrc
exec $SHELL
git clone git://github.com/sstephenson/ruby-build.git ~/.rbenv/plugins/ruby-build
echo 'export PATH="$HOME/.rbenv/plugins/ruby-build/bin:$PATH"' >> ~/.bashrc
exec $SHELL
git clone https://github.com/sstephenson/rbenv-gem-rehash.git ~/.rbenv/plugins/rbenv-gem-rehash
rbenv install 2.2.0
rbenv global 2.2.0
gem update --system
gem install bundle

# install ruby-related
apt-get -y install libsqlite3-dev
apt-get -y install libxslt-dev libxml2-dev
apt-get -y install nodejs 
apt-get -y install libmagickwand-dev

# install vim
apt-get -y install vim
