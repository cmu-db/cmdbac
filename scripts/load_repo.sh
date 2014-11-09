#!/bin/bash

table=db_webcrawler.crawler_repository
while read line
do
    name=$(echo $line | cut -f1 -d' ')
    echo $name
    echo "insert into $table (repo_type_id, full_name) values('Django', '$name')" | mysql -u fangyug -p1234
done < $1

