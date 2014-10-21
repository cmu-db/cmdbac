#!/bin/bash

rm db.sqlite3
python manage.py syncdb --noinput
cat init_commands.txt | python manage.py dbshell
