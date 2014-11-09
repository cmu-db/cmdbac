#!/bin/bash

table=db_webcrawler.crawler_package
while read line
do
    name=$(echo $line | cut -f1 -d=)
    version=$(echo $line | cut -f3 -d=)
    echo $name==$version
    echo "insert into $table (package_type_id, name, version) values('Django', '$name', '$version')" | mysql -u fangyug -p1234
done < $1



#load data local infile '~/packages_head.txt'
#into table test.crawler_package
#(name, version)
#set package_type_id = 'Django';
