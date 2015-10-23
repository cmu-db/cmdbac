keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']

def count_query(queries):
	ret = {}
	for keyword in keywords:
		ret[keyword] = 0
	ret['OTHERS'] = 0
	for query in queries:
		counted = False
		for keyword in keywords:
			if keyword in query:
				ret[keyword] += 1
				counted = True
		if not counted:
			ret['OTHERS'] += 1
	return ret
