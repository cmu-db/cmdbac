from baseanalyzer import *
from mysqlanalyzer import *
from postgresqlanalyzer import *

def get_analyzer(deployer):
	if deployer.get_database().name == 'MySQL':
		return MySQLAnalyzer(deployer)
	elif deployer.get_database().name == 'PostgreSQL':
		return PostgreSQLAnalyzer(deployer)
	elif deployer.get_database().name == 'SQLite3':
		return SQLite3Analyzer(deployer)
	else:
		return BaseAnalyzer(deployer)