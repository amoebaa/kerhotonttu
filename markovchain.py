import random
import codecs
import sys

class Markov(object):

	def __init__(self, file):
		self.cache = {}
		
		with codecs.open(file, encoding='ISO-8859-1') as f:
			text = f.read()
		
		text = self.clean_log(text)
		self.words = text.split(' ')
		self.word_size = len(self.words)
		self.database()
	
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
		
		return '\n'.join(returnstring) # still separate lines with newline, so we know when phrases end

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
		seed_word = self.words[seed]
		return self.generate_starting_with(seed_word, size, True)

    # generate a phrase using the seed word, max length of size. trusted is used if we are certain the word is within correct bounds
	def generate_starting_with(self, seed_word, size=50, trusted=False):
		if not trusted:
			if seed_word not in self.words:
				return ("Valitettavasti " + seed_word + " ei ole tunnettujen sanojen joukossa")
		index = self.words.index(seed_word)
		if index > len(self.words) - 2:
			return seed_word
		next_word = self.words[index + 1]
		w1, w2 = seed_word, next_word
		gen_words = []
		if '\n' in w1:
			return w1
		for i in range(size):
			gen_words.append(w1)
			if '\n' in w2:
				w2 = w2.split('\n')[0]
				break
			w1, w2 = w2, random.choice(self.cache[(w1,w2)])
		gen_words.append(w2)
		return ' '.join(gen_words)
		
	# generate a phrase of at least words words, maximum of size
	def generate_min_words(self, words=8, size=50):
		returnstring = ""
		while len(returnstring.split()) < words:
			returnstring = self.generate(size)
		return returnstring