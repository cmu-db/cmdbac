# Patterns
email_patterns = ['email', 'mail']
email_values = ['testuser@gmail.com']
username_patterns = ['username', 'name']
username_values = ['testuser']
password_patterns = ['password', 'pass']
password_values = ['Test1234--']
patterns = {
	'email': (email_patterns, email_values),
	'username': (username_patterns, username_values),
	'password': (password_patterns, password_values)
}

def match_any_pattern(name, patterns):
	return any(pattern in name.lower() for pattern in patterns)