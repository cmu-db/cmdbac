from subprocess import PIPE, Popen
from multiprocessing import Pool
import time
import traceback

def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True, stdout = PIPE, stderr = PIPE)
    stdout, stderr = p.communicate()
    return [int(p) for p in stdout.split()]

def run(args, cwd = None, shell = True, env = None, inputs = None):
    '''
    Run a command
    '''
    p = Popen(args, shell = shell, executable = '/bin/bash', stdin = PIPE, stdout = PIPE, stderr = PIPE, cwd = cwd, env = env)
    stdout, stderr = '', ''
    if inputs != None:
        for input in inputs:
            try:
                time.sleep(5)
                p.stdin.write(input)
            except:
                traceback.print_exc()
    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr

def run_command(command, timeout=0, input=None, cwd=None):
    if timeout > 0:
        commands = command.split('&&')
        commands[-1] = 'timeout {} {}'.format(timeout, commands[-1])
        command = '&& '.join(commands)
    return run(command, inputs = input, cwd = cwd)

def run_command_async(command, timeout=0, input=None, cwd=None):
    pool = Pool(processes=1)
    return pool.apply_async(run_command, [command, timeout, input, cwd]), pool