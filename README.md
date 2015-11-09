# db-webcrawler                                                                                                                                

Database Application Web Crawler. All command should be run in the project root directory, only support linux

## Install Requirements for Host Machine                                        
install virtualbox (4.3) (download .deb and use dpkg -i command or follow https://help.ubuntu.com/community/VirtualBox/Installation)

* python
* python-bs4
* vagrant
* unzip
* pip

install pip requirement packages (sudo pip install -r requirements.txt)         

## Environments                                                                 

set temperary pip user path (export PYTHONUSERBASE="/tmp/pip")                  

start virtualbox (vagrant up)                                                   
if host machine is under proxy, open bootstrap.sh script and set http_proxy to the proxy
The script install the requirements for virtual machine.                        
If the start process stuck, it maybe because of proxy problem.                  
The start of the script tries to configure proxy (setup http_proxy and proxy for apt-get) automatically, fix it if nessesary.

## Setup Database                                                               

create an database with utf8 character set. (especially these columns need utf8: character set. repository.description, repository.homepage, attempt.log)

load the data to the database (mysql xxx < db_webcrawler.sql)                   

change db_webcrawler/settings.py  DATABASE to the database to use               

## Crawler and Deployer                                                         

### Repository Crawler                                                          
start repository crawler (python run_repo_crawler.py)

### Repository Deployer                                                         
start repository deployer (python run_repo_deployer.py)                         
try deploy a repository(python run_repo_deployer.py <repository_name>)          
start repository deployer for a type (python run_repo_deployer.py <django or ror>)

deploy a repository using previous attempt id (python deploy.py <attempt_id>)   

### Package Crawler                                                             
start package_crawler (python run_package_crawler.py)                           

### Package Deployer                                                            
start package_deployer (python run_package_deployer.py)                         

## Website                                                                      

python manage.py runserver 0.0.0.0:8001                                         

## Warning                                                                      
the attempts_count field in repository table can only increase now, don't delete from entries attempt table, otherwise the attempt_count field in repository table is not correct.

## Todo                                                                         
Fill in the place holder for block_ports and unblock_ports functons in utils.py for security.
virtual machine ports in use:                                                   
port 22: for ssh                                                                
port 3000: for running ruby on rails apps                                       
port 8000: for running django apps                                              

The log system needs improvement

## Note:
1. Add SQL General Log(my.cnf, chown sql.log file)