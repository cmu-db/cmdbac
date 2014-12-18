# this file is take from stackoverflow
# http://stackoverflow.com/questions/1191374/subprocess-with-timeout

from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen

def run(args, cwd = None, shell = True, kill_tree = True, timeout = -1, env = None):
    '''
    Run a command with a timeout after which it will be forcibly
    killed.
    '''
    class Alarm(Exception):
        pass
    def alarm_handler(signum, frame):
        raise Alarm
    p = Popen(args, shell = shell, cwd = cwd, stdout = PIPE, stderr = PIPE, env = env)
    if timeout != -1:
        signal(SIGALRM, alarm_handler)
        alarm(timeout)
    try:
        stdout, stderr = p.communicate()
        if timeout != -1:
            alarm(0)
    except Alarm:
        pids = [p.pid]
        if kill_tree:
            pids.extend(get_process_children(p.pid))
        for pid in pids:
# process might have died before getting to this line
# so wrap to avoid OSError: no such process
            try: 
                kill(pid, SIGKILL)
            except OSError:
                pass
        return -9, '', ''
    return p.returncode, stdout, stderr

def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True, stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]
#
#if __name__ == '__main__':
#    print run('ls', shell = True, timeout = 3)
#    #print run('find', shell = True)

#import multiprocessing
#import time
#from utils import *
#
#import subprocess
#import threading
#
#class Command(object):
#    def __init__(self, cmd):
#        self.cmd = cmd
#        self.process = None
#
#    def run(self, timeout):
#        def target():
#            print 'Thread started'
#            self.process = subprocess.Popen(self.cmd, shell=True)
#            self.process.communicate()
#            print 'Thread finished'
#
#        thread = threading.Thread(target=target)
#        thread.start()
#
#        thread.join(timeout)
#        if thread.is_alive():
#            print 'Terminating process'
#            self.process.terminate()
#            thread.join()
#        print self.process.returncode
#
## bar
#def bar():
#    run_command('sleep 20')
##    for i in range(100):
##        print "Tick"
##        time.sleep(1)
#
#if __name__ == '__main__':
## Start bar as a process
#    command = Command('sleep 20')
#    command.run(timeout=3)
