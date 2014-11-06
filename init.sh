#!/bin/bash
db_name=test
#echo "INSERT INTO $db_name.crawler_status VALUES ('Found'), ('Deploying'), ('Deployed');" | mysql
echo "INSERT INTO $db_name.crawler_type VALUES ('Django'), ('Ruby on Rails');" | mysql
#echo "INSERT INTO $db_name.crawler_result VALUES ('Success'), ('Fail: Missing Dependency'), ('Fail: Other Reason'), ('Can Not Deploy');" | mysql
