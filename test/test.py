#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Zeyuan Shang
# @Date:   2015-12-22 23:55:52
# @Last Modified by:   Zeyuan Shang
# @Last Modified time: 2016-01-03 12:15:10
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

WAIT_TIME = 60

if __name__ == "__main__":
    database_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'username': 'root',
        'password': '',
        'name': 'drupal_app0'
    }
    try:
        browser = webdriver.PhantomJS()
        browser.get('http://127.0.0.1:8181/install.php?profile={}&welcome=done&locale=en'.format('openacademy'))
        
        # configure database
        try:
            print 'Configuring database ...'

            WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-mysql-database')))
            browser.find_element_by_id('edit-mysql-database').send_keys(database_config['name'])
            browser.find_element_by_id('edit-mysql-username').send_keys(database_config['username'])
            browser.find_element_by_id('edit-mysql-password').send_keys(database_config['password'])
            
            browser.find_element_by_class_name('fieldset-title').click()
            WebDriverWait(browser, WAIT_TIME).until(EC.visibility_of_element_located((By.ID, 'edit-mysql-host')))
            browser.find_element_by_id('edit-mysql-host').clear()
            browser.find_element_by_id('edit-mysql-host').send_keys(database_config['host'])
            browser.find_element_by_id('edit-mysql-port').send_keys(database_config['port'])
            browser.find_element_by_tag_name('form').submit()
        except:
            traceback.print_exc()
        
        # configure site
        try:
            print 'Configuring site ...'
            
            WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'edit-site-name')))
            browser.find_element_by_id('edit-site-name').send_keys(database_config['name'])
            browser.find_element_by_id('edit-site-mail').send_keys('admin@test.com')
            try:
                browser.find_element_by_id('edit-account-name').send_keys('admin')
                browser.find_element_by_id('edit-account-pass-pass1').send_keys('admin')
                browser.find_element_by_id('edit-account-pass-pass2').send_keys('admin')
            except:
                traceback.print_exc()
                pass
            browser.find_element_by_tag_name('form').submit()
        except:
            traceback.print_exc()

        # heuristical
        while True:
            WebDriverWait(browser, WAIT_TIME).until(EC.presence_of_element_located((By.ID, 'content')))
            
            # wait for progess
            if len(browser.find_elements_by_id('progress')) != 0:
                time.sleep(5)
                continue

            # get page title
            try:
                page_title = browser.find_element_by_class_name('page-title').text
            except:
                page_title = browser.find_element_by_id('page-title').text
            print page_title

            # select all checkboxes
            for option in browser.find_elements_by_class_name('form-checkbox'):
                if not option.is_selected():
                    option.click()

            # handle general user
            if len(browser.find_elements_by_id('edit-name')) != 0:
                print 'Configuring general user ...'
                browser.find_element_by_id('edit-name').send_keys('test')
                browser.find_element_by_id('edit-mail').send_keys('test@test.com')
                try:
                    browser.find_element_by_id('edit-pass-pass1').send_keys('test')
                    browser.find_element_by_id('edit-pass-pass2').send_keys('test')
                except:
                    pass

            # finish
            if len(browser.find_elements_by_xpath("//*[contains(text(), 'Congratulations')]")) != 0:
                break

            # submit
            try:
                browser.find_element_by_id('edit-submit').click()
            except:
                browser.find_element_by_tag_name('form').submit()
    except:
        traceback.print_exc()
    finally:
        browser.save_screenshot('/tmp/screenshot.png')
        browser.quit()



    

