keywords = ['SET', 'INSERT', 'UPDATE', 'DELETE']

def count_query(queries):
	ret = {}
	for keyword in keywords:
		ret[keyword] = 0
	for query in queries:
		for keyword in keywords:
			if query.startswith(keyword):
				ret[keyword] += 1
				break
	return ret