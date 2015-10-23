keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']

def count_query(queries):
	ret = {}
	for keyword in keywords:
		ret[keyword] = 0
	for query in queries:
		for keyword in keywords:
			if keyword in query:
				ret[keyword] += 1
	return ret
