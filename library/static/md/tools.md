# Command Line Tool Tutorial

### Install Requirements
To Start with, please install the required Python packages for running the command line tool. You can install them by pip as following
```sh
$ pip install requests
```

Please add enough permission for the main.py file as following
```sh
$ chmod +x main.py
```

### Get Attempt Information
You can get the sufficient information of an attempt by running this command:
```sh
$ ./main.py info -attempt ATTEMPT
```
where *ATTEMPT* is the id of the attempt you want to inquire. 

If you want to know more information, you can type this command to get a help message:
```sh
$ ./main.py info -h
```

### Running Benchmark
A lot of arguments are required to run the benchmark. You can type this command to get the full information:
```sh
./main.py benchmark -h
```
We have provide you with a comprehensive illustraions about the arguments:
```sh
usage: main.py benchmark [-h] [-attempt ATTEMPT] [-database DATABASE] [-host HOST] [-port PORT] [-name NAME] [-username USERNAME] [-password PASSWORD] [-num_threads NUM_THREADS] [-timeout TIMEOUT]

optional arguments:
  -h, --help            show this help message and exit
  -attempt ATTEMPT, --attempt ATTEMPT
                        the id of the attempt
  -database DATABASE, --database DATABASE
                        the database you are using, e.g. mysql
  -host HOST, --host HOST
                        the host address of your database server
  -port PORT, --port PORT
                        the port of your database server
  -name NAME, --name NAME
                        the name of your database
  -username USERNAME, --username USERNAME
                        the username of your database server
  -password PASSWORD, --password PASSWORD
                        the password of your database server
  -num_threads NUM_THREADS, --num_threads NUM_THREADS
                        the number of threads you want to use to submit forms
  -timeout TIMEOUT, --timeout TIMEOUT
                        the timeout for submitting forms
```

Then you can see the results if the arguments are correctly provided.
