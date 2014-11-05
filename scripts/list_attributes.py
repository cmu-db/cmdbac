import sys
import pkgutil
import os.path

filename = 'attributes.txt'
sys_path = '/usr/local/lib/python2.7/dist-packages'

def write_line(string, filename):
    with open(filename, "a") as myfile:
        myfile.write(string)
        myfile.write('\n')

def list_attributes(module[1]):
    attributes = dir(module[1])
    for attribute in attributes:
        write_line('#'+str(attribute), filename)
    
def list_modules(modules, base):
    for module in modules:
        write_line(str(module), filename)
        list_attributes(module)
        newBase = os.path.join(base, module[1])
        if module[2]:
            list_modules(pkgutil.iter_modules([os.path.join(sys_path, newBase)]), newBase)

if __name__ == "__main__":
    modules = pkgutil.iter_modules([sys_path])
    list_modules(modules, '')


