import random
import string

class Markov(object):

	def __init__(self, file):
		self.cache = {}
		self.table = string.maketrans("","")
		self.ATTEMPTS = 10
		
		with open(file) as f:
			text = f.read()
		
		text = self.clean_log(text)
		self.words = text.split(' ')
		self.word_size = len(self.words)
		self.database()
		self.braceleft = ('([{')
		self.braceright= (')]}')

	# learn a new row
	def learn(self, row):
		try:
			w = row
			if len(w[0]) > 1:
				w[0] = w[0][1:]
			else:
				w = w[1:]
			w.append('\n')
			for i in range(len(w) - 2):
				w1, w2, w3 = w[i], w[i+1], w[i+2]
				key = (w1, w2)
				if key in self.cache:
					self.cache[key].append(w3)
				else:
					self.cache[key] = [w3]  
			self.words.extend(w)
			self.word_size = len(self.words)
		except:
			pass

	#clean the log file from usual irc messages, and strip the leading timestamps and nicks
	def clean_log(self, text):
		returnstring = []
		rows = text.split('\n')
		
		for row in rows:
			if row.startswith("---") or len(row) < 10:
				continue
			str = row.split(None, 1)[1]
			if str.startswith("<"):
				returnstring.append(str.split(">",1)[1])
		
		return ' \n'.join(returnstring) # still separate lines with newline, so we know when phrases end

	# {word1, word2 -> word3} -structure
	def triples(self):
		if len(self.words) < 3:
			return
		
		for i in range(len(self.words) - 2):
			yield (self.words[i], self.words[i+1], self.words[i+2])
	
	# generate the dictionary
	def database(self):
		for w1, w2, w3 in self.triples():
			key = (w1, w2)
			if key in self.cache:
				self.cache[key].append(w3)
			else:
				self.cache[key] = [w3]

	# just generate any random pharase, max length of size
	def generate(self, size=50):
		seed = random.randint(0, self.word_size-3)
		return self.generate_with_index(seed, size)

	# generate a phrase using the seed index, max length of size
	def generate_with_index(self, seed, size=50):
		w1 = self.words[seed]
		w2 = self.words[seed + 1]
		if '\n' in w1:
			return "" # hack? maybe
		return self.generate_with(w1, w2, size)

	# generate a phrase using the seed words, max length of size
	def generate_with(self, word1, word2, size=50):
		w1 = word1
		w2 = word2
		gen_words = []
		for i in range(size):
			gen_words.append(w1)
			if '\n' in w2:
				w2 = ''
				break
			w1, w2 = w2, random.choice(self.cache[(w1,w2)])
		gen_words.append(w2)
		return ' '.join(gen_words)

	# generate a phrasing using two seed words, max length of size
	def generate_starting_phrase(self, seed_word1, seed_word2, size=50):
		key = (seed_word1, seed_word2)
		if (key not in self.cache):
			return ("Valitettavasti " + seed_word1 + " " + seed_word2 + " ei ole tunnettujen fraasien joukossa")
		return self.prettify(self.generate_with(seed_word1, seed_word2, size))

	# finds all the indexes for the supplied word (stripped from punctuation and capitalization)
	def find_indexes(self, seed_word):
		lst = []
		word = seed_word.lower()
		# find all the occurances
		for i in range(len(self.words) - 1):
			try:
				selfword = self.words[i].lower()
				if selfword == word or selfword.translate(self.table, string.punctuation) == word:
					if '\n' not in self.words[i + 1]:
						lst.append(i)
			except UnicodeEncodeError:
				if self.words[i] == word:
					if '\n' not in self.words[i + 1]:
						lst.append(i)
		return lst

	# generate a phrase using a random index from given choices
	def generate_starting_with(self, lst, size=50):
		index = random.choice(lst)
		if index > len(self.words) - 2:
			return seed_word
		return self.generate_with_index(index, size)

	# generate a phrase starting with a word, minuum on words lenght, maximumon size
	def generate_min_words_starting_with(self, seed_word, words=6, size=50):
		returnstring = ""
		indexes = self.find_indexes(seed_word)
		if len(indexes) < 1:
			return ("Valitettavasti " + seed_word + " ei ole tunnettujen sanojen joukossa")
		for i in range(self.ATTEMPTS):
			returnstring = self.generate_starting_with(indexes, size)
			if len(returnstring.split()) > words:
				break
		return self.prettify(returnstring)

	# generate a phrase of at least words words, maximum of size
	def generate_min_words(self, words=8, size=50):
		returnstring = ""
		while len(returnstring.split()) < words:
			returnstring = self.generate(size)
		return self.prettify(returnstring)

	# prettify text, adding matching quotation marks and braces
	def prettify(self, text, startsymbol=' ', endsymbol=' ', position=0):
		i = position
		phrase = text
		while i < len(phrase):
			# ignore basic :) ;) smileys!
			if i > 0 and phrase[i] == ')' and (phrase[i-1] == ':' or phrase[i-1] == ';'):
				i += 1
				continue
			elif phrase[i] in self.braceleft:
				terminator = self.braceright[self.braceleft.find(phrase[i])]
				response = self.prettify(phrase, phrase[i], terminator, i+1)
				if type(response) is list:
					i = response[0]
					phrase = response[1]
				else:
					i = response
			elif phrase[i] in self.braceright:
				if phrase[i] != endsymbol:
					terminator = self.braceleft[self.braceright.find(phrase[i])]
					phrase = self.addMissing(phrase, terminator, position, i, True)
					i += 1
				else:
					return i
			elif phrase[i] == '\"':
				if i == 0 or phrase[i-1] == ' ':
					response = self.prettify(phrase, '\"', '\"', i+1)
					if type(response) is list:
						i = response[0]
						phrase = response[1]
					else:
						i = response
				elif i == len(phrase) - 1 or phrase[i+1] == ' ':
					if endsymbol == '\"':
						return i
					else:
						phrase = self.addMissing(phrase, '\"', position, i, True)
						i += 1
			i += 1

		if endsymbol != ' ':
			phrase = self.addMissing(phrase, endsymbol, position, len(phrase), False)			
			return [len(phrase), phrase]

		return phrase
		
	def addMissing(self, phrase, missingSymbol, start, end, onleft=False):
		positions = list()
		inside = 0
		for i in range(start, end):
			if (phrase[i] == ' ' and inside == 0):
				positions.append(i)
			elif i > 0 and phrase[i] == ')' and (phrase [i-1] == ':' or phrase[i-1] == ';'):
				continue
			elif phrase[i] in self.braceleft:
				inside -= 1
			elif phrase[i] in self.braceright:
				inside += 1
			elif phrase[i] == '\"':
				if i == 0 or phrase[i-1] == ' ':
					inside -= 1
				elif i == len(phrase) - 1 or phrase[i+1] == ' ':
					inside += 1
		if onleft == True:
			positions.append(start - 1)
		else:
			positions.append(end)
		pos = positions[random.randint(0, len(positions) - 1)]
		if onleft == True:
			pos += 1
		return phrase[:pos] + missingSymbol + phrase[pos:]
