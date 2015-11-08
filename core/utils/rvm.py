import os
import re

from run import run_command
from file import cd

def get_ruby_versions():
    command = 'source /usr/local/rvm/scripts/rvm && rvm list'
    output = run_command(command)
    versions = []
    for line in output[1].split('\n'):
        s = re.search('ruby-(.+) \[', line)
        if s:
            versions.append(s.group(1))
    return versions

def use_ruby_version(version):
    command = 'source /usr/local/rvm/scripts/rvm && rvm --default use {}'.format(version)
    return run_command(command)