# this file is take from stackoverflow
# http://stackoverflow.com/questions/1191374/subprocess-with-timeout

from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen
from multiprocessing import Pool

def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True, stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]

def run(args, cwd = None, shell = True, kill_tree = True, timeout = -1, env = None):
    '''
    Run a command with a timeout after which it will be forcibly
    killed.
    '''
    class Alarm(Exception):
        pass
    def alarm_handler(signum, frame):
        raise Alarm
    p = Popen(args, shell = shell, cwd = cwd, stdout = PIPE, stderr=PIPE, env = env)
    if timeout != -1:
        signal(SIGALRM, alarm_handler)
        alarm(timeout)
    stdout, stderr = '', ''
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
                print pid
            except OSError:
                pass
        return -9, '', ''
    return p.returncode, stdout, stderr

def run_command(command, timeout=1000):
    return run(command, timeout=timeout)

def run_command_async(command, timeout=1000):
    pool = Pool(processes=1)
    return pool.apply_async(run_command, [command, timeout])