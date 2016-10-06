from bs4 import BeautifulSoup
import requests, re, os




def compare_answer(l_student, l_web):
	set_names = ['FIRST SET', 'FOLLOW SET', 'FIRST+ SET']
	for i, (ds, dw) in enumerate(zip(l_student, l_web)):
		if len(ds) < len(dw):
			print "ERROR: the number of elements in your %s is less than that of the web" % set_names[i]
		for symbol, set_ in ds.items():
			if symbol not in dw:
				print "warning: the %s of the symbol (%s) in your solution is not presented in the web solution" %(set_names[i], symbol)
			else:
				if set_ != dw[symbol]:
					#The predict set do not have epsilon while the first+ set do
					if not (i == 2 and set_ - dw[symbol] == {'EPSILON'}):
						print "Error: for the %s of the symbol (%s), your solution differ from the web" %(set_names[i], symbol)
						print "	Yours", set_
						print "	Web", dw[symbol]
						print

def file_to_sets(fh):
	patterns = [r'first set', r'follow set', r'first\+ set']
	set_list = []
	for line in fh:
		for p in patterns:
			if re.search(p, line, re.IGNORECASE):
				set_list.append(match_element(fh))
	return set_list
			

def match_element(iter):
	#should look like    symbol : {symbol, symbol}
	#symbol list must be separated by', '
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


def read(fname):
	try:
		fh = open(fname)
		return fh
	except IOError as e:
		raise SystemExit("I/O error({0}): {1}".format(e.errno, e.strerror))

def parse_answer(data):
	#print data
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
		# print
		#print symbol2set
	return set_list

def fetch_answer(ebnf):
	payload = {'grammar' : ebnf}
	with requests.session() as s:
		checker_url = 'http://hackingoff.com/compilers/predict-first-follow-set'
		response_post = s.post(checker_url, data=payload)
		return response_post.text

# def find_files():
# 	import fnmatch
# 	import os
# 	for file in os.listdir('.'):
# 		if fnmatch.fnmatch(file, '*.txt'):


def mbnf_2_ebnf(fh):
	#ebnf = mbnf.replace(':', '->').replace(';','').replace('epsilon','EPSILON')
	mbnf = fh.read()
	symbol_reg = r'[\n\s]*([a-zA-Z0-9]+)[\s\n]*'
	rhs_reg = r'[\n\s]*([a-zA-Z0-9]+)([a-zA-Z0-9 ]*)\n*'
	ir = []
	mbnf = re.sub(re.compile("//.*?\n" ) ,"" ,mbnf)
	plist = mbnf.split(';')
	for p in plist:
		split_p = p.split(':')
		if len(split_p) == 2:
			left, right = p.split(':')
			rhss = right.split('|')
			#print "left: ", left
			lhs = re.match(symbol_reg, left).group(1)
			rhs_rep = []
			for rhs in rhss:
				#print "original rhs", rhs
				match = re.match(rhs_reg, rhs)
				rhs_rep.append(match.group(1) + match.group(2))
			new_rep = "%s -> %s" %(lhs, ' | '.join(rhs_rep))
			ir.append(new_rep)
	ebnf = re.sub('epsilon', 'EPSILON', '\n'.join(ir), re.IGNORECASE)
	return ebnf


def check_answer(folder_path, student_folder):
	for f in find_files(folder_path):
		print "now Comparing file " + f
		answer_web = parse_answer(fetch_answer(mbnf_2_ebnf(read(f))))
		student_path = os.path.join(student_folder, os.path.basename(f))
		answer_student = file_to_sets(read(student_path))
		compare_answer(answer_student, answer_web)
		
		print "=========================="





def find_files(path):
	
	matches = []
	for root, dirnames, filenames in os.walk(path):
		for basename in filenames:
			if basename.endswith(('.ll1', '.nonll1')):
				yield os.path.join(root, basename)







check_answer('./grammars/', './yaml/')


f1 = file_to_sets(read('chris_result.txt'))
f2 = parse_answer(fetch_answer(mbnf_2_ebnf(read('ceg-rr-simple.ll1'))))
compare_answer(f1, f2)

