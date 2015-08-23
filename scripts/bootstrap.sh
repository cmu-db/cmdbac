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

# The output of all these installation steps is noisy. With this utility
# the progress report is nice and concise.

function install {
    echo Installing $1
    shift
    apt-get -y install "$@" >/dev/null 2>&1
}

echo updating package information
install 'apt-repository' software-properties-common python-software-properties
add-apt-repository ppa:chris-lea/node.js
apt-get -y update >/dev/null 2>&1

install 'development tools' build-essential unzip curl openssl libssl-dev libcurl4-openssl-dev zlib1g zlib1g-dev 
install 'Python' python-dev python-software-properties

# install Ruby
gpg --keyserver hkp://keys.gnupg.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
curl -sSL https://get.rvm.io | bash -s stable
source /usr/local/rvm/scripts/rvm
rvm install 2.2.2
rvm use 2.2.2 --default
gem install bundler
gem install rails
gem install bundle

echo -e "\n- - - - - -\n"
echo -n "Should be sqlite 3.8.1 or higher: sqlite "
sqlite3 --version
echo -n "Should be rvm 1.26.11 or higher:         "
rvm --version | sed '/^.*$/N;s/\n//g' | cut -c 1-11
echo -n "Should be ruby 2.2.2:                "
ruby -v | cut -d " " -f 2
echo -n "Should be Rails 4.2.1 or higher:         "
rails -v
echo -e "\n- - - - - -\n"

# install pip
wget https://bootstrap.pypa.io/get-pip.py -O /home/vagrant/get-pip.py
python /home/vagrant/get-pip.py
echo 'export PYTHONUSERBASE="/home/vagrant/pip"' >> /home/vagrant/.bashrc

# install Beautifulsoup
echo installing Beautifulsoup
pip install BeautifulSoup4

# install Django
echo installing Djano
pip install django

# install dependencies
install 'Git' git
install 'SQLite' sqlite3 libsqlite3-dev
install 'PostgreSQL' postgresql postgresql-contrib libpq-dev
debconf-set-selections <<< "mysql-server mysql-server/root_password password ''"
debconf-set-selections <<< "mysql-server mysql-server/root_password_again password ''"
install 'MySQL' mysql-server libmysqlclient-dev
pip install MySQL-python
install 'Nodejs' nodejs
install 'Nokogiri dependencies' libxml2 libxml2-dev libxslt1-dev imagemagick libmagickwand-dev
apt-get -f -y install >/dev/null 2>&1

# Needed for docs generation.
update-locale LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8 LC_ALL=en_US.UTF-8

echo 'all set, rock on!'