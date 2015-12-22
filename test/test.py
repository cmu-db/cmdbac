#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2015-12-22 23:55:52
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2015-12-23 01:41:32
from selenium import webdriver
import time
import traceback

STEP_SLEEP_TIME = 15

if __name__ == "__main__":
    browser = webdriver.PhantomJS()
    browser.get('http://127.0.0.1:8181/install.php')
    
    # select profile
    try:
        browser.find_element_by_id('edit-profile--4').click()
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    time.sleep(STEP_SLEEP_TIME)

    # select locale
    try:
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    time.sleep(STEP_SLEEP_TIME)

    database_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': '',
        'name': 'drupal_app0'
    }
    
    # configure database
    try:
        browser.find_element_by_id('edit-mysql-database').send_keys(database_config['name'])
        browser.find_element_by_id('edit-mysql-username').send_keys(database_config['username'])
        browser.find_element_by_id('edit-mysql-password').send_keys(database_config['password'])
        browser.find_element_by_class_name('fieldset-title').click()
    except:
        pass
    
    time.sleep(STEP_SLEEP_TIME)
    
    try:
        browser.find_element_by_id('edit-mysql-host').clear()
        browser.find_element_by_id('edit-mysql-host').send_keys(database_config['host'])
        browser.find_element_by_id('edit-mysql-port').send_keys(database_config['port'])
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    time.sleep(STEP_SLEEP_TIME)

    # configure site
    try:
        browser.find_element_by_id('edit-site-name').send_keys(database_config['name'])
        browser.find_element_by_id('edit-site-mail').send_keys('admin@test.com')
        browser.find_element_by_id('edit-account-name').send_keys('admin')
        browser.find_element_by_id('edit-account-pass-pass1').send_keys('admin')
        browser.find_element_by_id('edit-account-pass-pass2').send_keys('admin')
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    time.sleep(STEP_SLEEP_TIME)

    # feature set
    try:
        for option in browser.find_elements_by_class_name('form-checkbox'):
            if not option.is_selected():
                option.click()
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    time.sleep(STEP_SLEEP_TIME)

    # layout
    try:
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    try:
        browser.find_element_by_id('edit-name').send_keys('test')
        browser.find_element_by_id('edit-mail').send_keys('test@test.com')
        try:
            browser.find_element_by_id('edit-pass-pass1').send_keys('test')
            browser.find_element_by_id('edit-pass-pass2').send_keys('test')
        except:
            pass
        browser.find_element_by_tag_name('form').submit()
    except:
        pass

    time.sleep(STEP_SLEEP_TIME)
    print browser.current_url
    browser.save_screenshot('/tmp/screenshot.png')



    

