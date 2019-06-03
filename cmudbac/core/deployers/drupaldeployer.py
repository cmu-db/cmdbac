import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import logging
import re
import time
import traceback
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .basedeployer import BaseDeployer
from library.models import *
import utils

## =====================================================================
## LOGGING CONFIGURATION
## =====================================================================
LOG = logging.getLogger()

## =====================================================================
## SETTINGS
## =====================================================================
WAIT_TIME_SHORT = 10
WAIT_TIME_LONG = 300
ERROR_THRESHOLD = 5

## =====================================================================
## Drupal DEPLOYER
## =====================================================================
class DrupalDeployer(BaseDeployer):
    def __init__(self, repo, database, deploy_id, database_config = None):
        BaseDeployer.__init__(self, repo, database, deploy_id, database_config)
        if database_config == None:
            self.database_config['name'] = 'drupal_app' + str(deploy_id)
    ## DEF

    def configure_settings(self, path):
        pass
    ## DEF

    def get_main_url(self):
        return 'http://127.0.0.1:{}/'.format(self.port)
    ## DEF

    def drupal_has_installed(self):
        return self.installed

    def configure_profile(self):
        self.installed = False
        error_count = 0

        def check_drupal_status(deployer):
            browser = webdriver.PhantomJS()

            while True:
                time.sleep(WAIT_TIME_SHORT)

                if self.installed:
                    break

                try:
                    browser.get('http://127.0.0.1:{port}/install.php'.format(port = deployer.port))
                    WebDriverWait(browser, WAIT_TIME_SHORT).until(EC.presence_of_element_located((By.ID, 'content')))

                    # wait for progess
                    if len(browser.find_elements_by_id('progress')) != 0:
                        time.sleep(5)
                        continue

                    try:
                        page_title = browser.find_element_by_class_name('page-title').text
                    except:
                        try:
                            page_title = browser.find_element_by_id('page-title').text
                        except:
                            page_title = 'Unkown page'
                    if 'Drupal already installed' in page_title:
                        self.installed = True
                        break
                except:
                    pass

            browser.quit()

        def get_all_profiles():
            browser = webdriver.PhantomJS()
            browser.get('http://127.0.0.1:{port}/install.php'.format(port = self.port))
            WebDriverWait(browser, WAIT_TIME_LONG).until(EC.presence_of_element_located((By.ID, 'content')))

            profiles = []
            for element in browser.find_elements_by_class_name('form-radio'):
                profiles.append(element.get_attribute('value'))

            browser.quit()

            return profiles


        try:
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(800, 600))
            display.start()

            profiles = get_all_profiles()
            profile = self.repo.repo_name()
            if not self.repo.name.startswith('drupal/'):
                if profile not in profiles:
                    profile = profiles[0]
            LOG.info('Profile: {}'.format(profile))

            browser = webdriver.PhantomJS()
            browser.get('http://127.0.0.1:{port}/install.php?profile={profile}&welcome=done&locale=en'.format(port = self.port, profile = profile))

            t = threading.Thread(target = check_drupal_status, args = (self, ))
            t.daemon = True
            t.start()

            database_tag_name = {
                'MySQL': 'mysql',
                'PostgreSQL': 'pgsql',
                'SQLite3': 'sqlite'
            }.get(self.database.name, 'mysql')

            # heuristical
            while True:
                if self.drupal_has_installed():
                    break

                try:
                    WebDriverWait(browser, WAIT_TIME_SHORT).until(EC.presence_of_element_located((By.ID, 'content')))
                except:
                    break

                try:
                    browser.find_element_by_class_name('error')
                    error_count += 1
                    if error_count > ERROR_THRESHOLD:
                        break
                    else:
                        browser.refresh()
                except:
                    pass

                # wait for progess
                if len(browser.find_elements_by_id('progress')) != 0:
                    time.sleep(5)
                    continue

                try:
                    page_title = browser.find_element_by_class_name('page-title').text
                except:
                    try:
                        page_title = browser.find_element_by_id('page-title').text
                    except:
                        page_title = 'Unkown page'
                LOG.info(page_title)
                if 'Drupal already installed' in page_title:
                    break

                # select all checkboxes
                for option in browser.find_elements_by_class_name('form-checkbox'):
                    if option.is_displayed() and not option.is_selected():
                        option.click()

                # click field set
                if len(browser.find_elements_by_class_name('fieldset-title')) != 0:
                    browser.find_element_by_class_name('fieldset-title').click()

                # handle database
                if len(browser.find_elements_by_id('edit-driver-{}'.format(database_tag_name))) != 0:
                    browser.find_element_by_id('edit-driver-{}'.format(database_tag_name)).click()
                    browser.find_element_by_id('edit-{}-database'.format(database_tag_name)).send_keys(self.database_config['name'])
                    browser.find_element_by_id('edit-{}-username'.format(database_tag_name)).send_keys(self.database_config['username'])
                    browser.find_element_by_id('edit-{}-password'.format(database_tag_name)).send_keys(self.database_config['password'])
                # handle site
                elif len(browser.find_elements_by_id('edit-site-name')) != 0:
                    browser.find_element_by_id('edit-site-name').send_keys(self.database_config['name'])
                    browser.find_element_by_id('edit-site-mail').send_keys('admin@test.com')
                    try:
                        browser.find_element_by_id('edit-account-name').send_keys('admin')
                        browser.find_element_by_id('edit-account-pass-pass1').send_keys('admin')
                        browser.find_element_by_id('edit-account-pass-pass2').send_keys('admin')
                    except:
                        pass
                # handle general user
                elif len(browser.find_elements_by_id('edit-name')) != 0:
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

            self.installed = True
        except Exception as e:
            LOG.exception(e)
            browser.save_screenshot('/tmp/screenshot.png')
        finally:
            browser.quit()
            display.stop()

        return self.installed
    ## DEF

    def sync_server(self, path):
        LOG.info('Syncing server ...')
        utils.run_command_async('drush ss', input=['0.0.0.0\n', '{}\n'.format(self.port)], cwd=path)

        time.sleep(WAIT_TIME_SHORT)

        return self.configure_profile()
    ## DEF

    def run_server(self, path):
        self.configure_network()
    ## DEF

    def get_runtime(self):
        out = utils.run_command('php -v')
        return {
            'executable': 'php',
            'version': out[1].split('\n')[0].split()[1]
        }
    ## DEF

    def try_deploy(self, deploy_path):
        LOG.info('Configuring settings ...')
        self.kill_server()
        self.clear_database()
        self.configure_settings(deploy_path)
        self.runtime = self.get_runtime()
        LOG.info(self.runtime)

        self.attempt.database = self.get_database()
        LOG.info('Database: ' + self.attempt.database.name)

        if not self.sync_server(deploy_path):
            return ATTEMPT_STATUS_RUNNING_ERROR

        self.run_server(deploy_path)
        time.sleep(5)

        attemptStatus = self.check_server()

        return attemptStatus
    ## DEF

    def deploy_repo_attempt(self, deploy_path):
        install_phps = utils.search_file(deploy_path, 'install.php')
        if len(install_phps) == 0:
            return ATTEMPT_STATUS_MISSING_REQUIRED_FILES
        base_dir = sorted([os.path.dirname(install_php) for install_php in install_phps])[0]

        self.setting_path = base_dir

        return self.try_deploy(base_dir)
    ## DEF

## CLASS