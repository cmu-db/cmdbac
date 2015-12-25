#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2015-12-22 23:55:52
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2015-12-25 12:25:01
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

WAIT_TIME = 15

if __name__ == "__main__":
    browser = webdriver.PhantomJS()
    browser.get('http://127.0.0.1:8181/install.php')
    
    browser.save_screenshot('/tmp/screenshot.png')
    # select profile
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-profile--4')))
        browser.find_element_by_id('edit-profile--4').click()
        browser.find_element_by_tag_name('form').submit()
        print 'Selecting profile ...'
    except:
        traceback.print_exc()
        pass

    browser.save_screenshot('/tmp/screenshot.png')
    # select locale
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        browser.find_element_by_tag_name('form').submit()
        print 'Selecting locale ...'
    except:
        traceback.print_exc()
        pass

    database_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': 'root',
        'name': 'drupal_app0'
    }
    
    browser.save_screenshot('/tmp/screenshot.png')
    # configure database
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-mysql-database')))
        browser.find_element_by_id('edit-mysql-database').send_keys(database_config['name'])
        browser.find_element_by_id('edit-mysql-username').send_keys(database_config['username'])
        browser.find_element_by_id('edit-mysql-password').send_keys(database_config['password'])
        browser.find_element_by_class_name('fieldset-title').click()
    except:
        traceback.print_exc()
        pass
    
    browser.save_screenshot('/tmp/screenshot.png')
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-mysql-host')))
        browser.find_element_by_id('edit-mysql-host').clear()
        browser.find_element_by_id('edit-mysql-host').send_keys(database_config['host'])
        browser.find_element_by_id('edit-mysql-port').send_keys(database_config['port'])
        browser.find_element_by_tag_name('form').submit()
        print 'Configuring database ...'
    except:
        traceback.print_exc()
        pass

    browser.save_screenshot('/tmp/screenshot.png')
    # configure site
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-site-name')))
        browser.find_element_by_id('edit-site-name').send_keys(database_config['name'])
        browser.find_element_by_id('edit-site-mail').send_keys('admin@test.com')
        browser.find_element_by_id('edit-account-name').send_keys('admin')
        browser.find_element_by_id('edit-account-pass-pass1').send_keys('admin')
        browser.find_element_by_id('edit-account-pass-pass2').send_keys('admin')
        browser.find_element_by_tag_name('form').submit()
        print 'Configuring site ...'
    except:
        traceback.print_exc()
        pass

    browser.save_screenshot('/tmp/screenshot.png')
    # feature set
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, 'form-checkbox')))
        for option in browser.find_elements_by_class_name('form-checkbox'):
            if not option.is_selected():
                option.click()
        browser.find_element_by_tag_name('form').submit()
        print 'Configuring feature set ...'
    except:
        traceback.print_exc()
        pass

    browser.save_screenshot('/tmp/screenshot.png')
    # layout
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        browser.find_element_by_tag_name('form').submit()
        print 'Configuring layout ...'
    except:
        traceback.print_exc()
        pass

    browser.save_screenshot('/tmp/screenshot.png')
    # general user
    try:
        WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-name')))
        browser.find_element_by_id('edit-name').send_keys('test')
        browser.find_element_by_id('edit-mail').send_keys('test@test.com')
        try:
            browser.find_element_by_id('edit-pass-pass1').send_keys('test')
            browser.find_element_by_id('edit-pass-pass2').send_keys('test')
        except:
            pass
        browser.find_element_by_tag_name('form').submit()
        print 'Configuring general user ...'
    except:
        traceback.print_exc()
        pass

    time.sleep(WAIT_TIME * 2)
    browser.save_screenshot('/tmp/screenshot.png')
    browser.quit()



    

