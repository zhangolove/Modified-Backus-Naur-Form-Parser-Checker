from bs4 import BeautifulSoup
import requests, re, os




def mbnf_2_ebnf(fh):
	"""
	Input: a file handle that contains a language of mbnf grammar
	Output: a string of equivalent language in ebnf form
	"""
	mbnf = fh.read()
	symbol_reg = r'[\n\s]*([a-zA-Z0-9]+)[\s\n]*'
	rhs_reg = r'[\n\s]*([a-zA-Z0-9]+)([a-zA-Z0-9\s]*)\n*'
	ir = []
	mbnf = re.sub(re.compile("//.*?\n" ) ,"" ,mbnf)
	plist = mbnf.split(';')
	for p in plist:
		split_p = p.split(':')
		if len(split_p) == 2:
			left, right = p.split(':')
			rhss = right.split('|')
			lhs = re.match(symbol_reg, left).group(1)
			rhs_rep = []
			for rhs in rhss:
				match = re.match(rhs_reg, rhs)
				str = match.group(1) + match.group(2)
				str = str.replace('\n', '')
				re.sub('[\s\t]+', ' ', str)
				rhs_rep.append(str)
			new_rep = "%s -> %s" %(lhs, ' | '.join(rhs_rep))
			ir.append(new_rep)
	ebnf = re.sub(r'epsilon', r'EPSILON', '\n'.join(ir), flags=re.IGNORECASE)
	return ebnf

def fetch_answer_from_web(ebnf):
	"""
	Input: a string in ebnf grammar
	Output: an html file returned by the hackingoff website that contains the answer
	"""
	payload = {'grammar' : ebnf}
	with requests.session() as s:
		checker_url = 'http://hackingoff.com/compilers/predict-first-follow-set'
		response_post = s.post(checker_url, data=payload)
		return response_post.text

def parse_answer_from_web(data):
	"""
	Parse the answer from the html file
	Output: A list of dictionary [first, follow, first+]
			each dictionary is in the form of {symbol: set([symbol...])}
	"""

	soup = BeautifulSoup(data, "html.parser")
	tables = soup.find_all(class_='set-table')
	set_list = []
	translate_table = {u'$' : '<EOF>', u'\u03b5': 'EPSILON'}
	for table in tables:
		rows = table.find_all('tr')[1:]
		symbol2set = {}
		for row in rows:
			tds = map(lambda x: x.text, row.find_all('td'))
			symbol = tds[0] if tds[0] not in translate_table else translate_table[tds[0]]
			s_set = {w if w not in translate_table else translate_table[w] for w in tds[-1].split(', ')}
			symbol2set[symbol] = s_set
		set_list.append(symbol2set) 
	return set_list



def parse_answer_from_student(fh):
	"""
	fh should be written in the following format:

		First set
			symbol_name_a: {symbol_name_1, symbol_name_2....symbol_name_n}
			symbol_name_b: {symbol_name_1, symbol_name_2....symbol_name_n}

		Follow set
			symbol_name_a: {symbol_name_1, symbol_name_2....symbol_name_n}
			symbol_name_b: {symbol_name_1, symbol_name_2....symbol_name_n}

		First+ set
			symbol_name_a: {symbol_name_1, symbol_name_2....symbol_name_n}
			symbol_name_b: {symbol_name_1, symbol_name_2....symbol_name_n}

	The keywords are "First set", "Follow set", and "First+ set", the program use these
	keywords to determine which set you are referring to. The sections must be in the above
	order and separated by a blank line.
    """
	patterns = [r'first set', r'follow set', r'first\+ set']
	set_list = []
	for line in fh:
		for p in patterns:
			if re.search(p, line, re.IGNORECASE):
				set_list.append(match_element(fh))
	return set_list
			

def match_element(iter):
	# helper function to parse all the element for a set
	pattern = r'\s*([a-zA-Z0-9<>]+)\s*:\s*{([a-zA-Z0-9,<>\s]+)}'
	symbol2set = {}
	while True:
		try:
			line = next(iter)
		except StopIteration:
			return symbol2set
		match = re.match(pattern, line)
		if not match:
			break
		else:
			s = match.group(1)
			set_ = set(match.group(2).split(', '))
			symbol2set[s] = set_
	return symbol2set



def find_files(path):
	# returns file ending with '.ll1' or '.nonll1' in a folder
	matches = []
	for root, dirnames, filenames in os.walk(path):
		for basename in filenames:
			if basename.endswith(('.ll1', '.nonll1')):
				yield os.path.join(root, basename)


def read(fname):
	# return an opened file
	try:
		fh = open(fname)
		return fh
	except IOError as e:
		raise SystemExit("I/O error({0}): {1}".format(e.errno, e.strerror))

def compare_answer(l_student, l_web):
	"""
	This function will compare two lists of dictionary
	l_student = [d_first, d_follow, d_first_plus]
	d_first = {symbol_name: set of string}
	"""
	set_names = ['FIRST SET', 'FOLLOW SET', 'FIRST+ SET']
	ret = True
	for i, (ds, dw) in enumerate(zip(l_student, l_web)):
		if len(ds) < len(dw):
			print "ERROR: the number of elements in your %s is less than that of the web" % set_names[i]
			ret = False
		for symbol, set_ in ds.items():
			if symbol not in dw:
				print "warning: the %s of the symbol (%s) in your solution is not presented in the web solution" %(set_names[i], symbol)
			else:
				if set_ != dw[symbol]:
					#The predict set do not have epsilon while the first+ set do
					#if not (i == 2 and set_ - dw[symbol] == {'EPSILON'}):
					#The web solution will use empty string to represent '<EOF>' for the goal symbol
					if i != 2 and not (set_ == {'<EOF>'} and dw[symbol] == {u''}) :
						print "Error: for the %s of the symbol (%s), your solution differ from the web" %(set_names[i], symbol)
						print "	Yours", set_
						print "	Web", dw[symbol]
						print
						ret = False
	return ret


def check_answer(grammar_path, student_folder):
	"""
	This function will check the first, follow sets for files in grammar_path against 
	the answer in 'http://hackingoff.com/compilers/predict-first-follow-set'
	Input:
		grammar_path: a directory that contains files ending with .ll1 and .nonll1 files
					  Each file should include a language of mbnf grammar
		student_folder: a directory that contains files ending with .ll1 and .nonll1 files;
						Each format of file content is specified in parse_answer_from_student; 
						The base filenames have to be a one-to-one map from the grammar folder
						For example, the answer for grammar_path/xx/iloc.ll1 must have the 
						filename of student_folder/iloc.ll1.
	"""

	for f in find_files(grammar_path):
		print "now Comparing file " + f
		answer_web = parse_answer_from_web(fetch_answer_from_web(mbnf_2_ebnf(read(f))))
		student_path = os.path.join(student_folder, os.path.basename(f))
		answer_student = parse_answer_from_student(read(student_path))
		if not compare_answer(answer_student, answer_web):
			print "The ebnf form: "
			print mbnf_2_ebnf(read(f))
		print "=========================="


check_answer('./grammars/', './yaml/')


