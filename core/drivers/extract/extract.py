def extract_form():
	pass

def extract_all_forms(url):
	utils.remove_file(os.path.join(os.path.dirname(__file__), 'forms.json'))
	out = utils.run_command('{} && {}'.format(
		utils.cd(os.path.join(os.path.dirname(__file__))),
		'scrapy crawl form -o forms.json -a start_url="{}"'.format(url)))
		
	with open(os.path.join(os.path.dirname(__file__), 'forms.json')) as json_forms:
		try:
			forms = json.load(json_forms)
		except:
			print traceback.print_exc()
			forms = []

	return forms