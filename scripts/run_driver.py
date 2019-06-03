#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, "core"))

import json
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmudbac.settings")
import django
django.setup()

from drivers import *

def main():
    if len(sys.argv) < 2:
        return
    main_url = sys.argv[1]
    if len(sys.argv) >= 3:
        database_name = sys.argv[2]
    else:
        database_name = 'MySQL'
    database = Database.objects.get(name = database_name)

    print('Driving ...')
    base_driver = BaseDriver(main_url, database, 'test')
    try:
        driverResult = base_driver.drive()
    except:
        traceback.print_exc()
        driverResult = {}

    print('Random Walking ...')

    try:
        random_driver = RandomDriver(base_driver)
        random_driver.submit_forms()
        print(random_driver.forms)
        for form in random_driver.forms:
            if any(random_driver.equal_form(form, ret_form) for ret_form in driverResult['forms']):
                continue
            driverResult['forms'].append(form)
    except Exception as e:
        traceback.print_exc()

    print('Driver Results:')
    print(json.dumps(driverResult, indent=4, sort_keys=True))

if __name__ == '__main__':
    main()
