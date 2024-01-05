import re
from sys import stderr
from math import ceil

indent_in = 4
indent_out = 3

esc = '\x1b'	# The escape character
csi = esc + '['	# Control Sequence Introducer, used for terminal control sequences
def sgr(n):	# Return a string that when printed will send a Select Graphic Rendition command to the terminal. n should be an integer indicating the display mode to select
	return(csi + str(n) + 'm')
def with_sgr(n, string):	# Return a string containing the given string with graphic rendition code n, and a code that resets the terminal after
	return(sgr(n)+string+sgr(0))

re_word_break = re.compile('(?<=\S)[ \t]+|(?<=\n)')
re_nospace = re.compile('\S')

def justify_line(words, words_width, line_width):
	if not words:
		return ''
	if words[-1] and words[-1][-1] == '\n': # This is the last line of the paragraph, don't justify
		return ' '.join(words)
	s = ''
	spaces = line_width - words_width	# The total n of spaces we need to add
	word_breaks = len(words)-1	# Number of word breaks in the line
	if(word_breaks > 0):
		base_spaces = spaces // word_breaks	# Number of spaces for each word break
		leftover_spaces = spaces % word_breaks	# Extra spaces left over when n of word breaks doesn't evenly divide number of spaces; we'll add an extra space to only the first however many word breaks
		for i in range(word_breaks):
			s += words[i]
			s += ' '*base_spaces
			if(i < leftover_spaces): s += ' '
	s += words[-1]
	s += '\n'
	return s

def find_page_with_word(word_n, index):
	for i in range(len(index)):
		if index[i] > word_n:
			return i
	return index[-1]

def split_words_into_pages(words, width, lines, min_width):
#;This function takes an array of words, as is returned from split_text_into_words(), and splits them into pages of the specified width and height. The min_width argument is used in hyphenating words; if moving the next word to the next line would make the current line shorter than min_width, then that word will instead be broken up with a hyphen and split between the lines.
	word_n = 0
	pages = []
	word_index = []
	indent = 0
	while word_n < len(words):
		page, _, word_n, indent = justify_words(words, width, word_n, min_width, lines, indent)
		pages.append(page)
		word_index.append(word_n)
	return (pages, word_index)

	
def split_text_into_words(text):
# This function splits a string of text into words. It will return an array of strings that each contain one word
	return re_word_break.split(text)
#	words = text.split(' ')
#	i = 0
#	while i < len(words):
#		try:
#			lineb = words[i].index('\n')
#			words.insert(i+1, words[i][lineb+1:])
#			words[i] = words[i][:lineb+1]
#		except ValueError:
#			pass
#		i += 1
#	return words

def get_word_and_indent(word):
	# If <word> is a string containing a word that may be preceeded by whitespace, this function extracts the word and returns the number of spaces to indent in the output (equal to the number of leading whitespace characters / indent_in, rounded up, all multiplied by indent_out). Returns a 2-tuple of the word and indent as an integer. Used by justify_words to handle indenting
	start_match = re_nospace.search(word)
	if start_match:
		start = start_match.start()
		extracted_word = word[start:]
		indent = indent_out*ceil(start/indent_in)
		return extracted_word, indent
	else:
		return '', 0

def justify_words(words, width, start_word = 0, min_width = 1, max_lines = None, start_indent = 0):
# This funciton goes through a list of words and assembles them into a page of justified lines of the specified width (<width>) and height (<max_lines>).
# words: list of words, some of which will be assembled into a justified page
# width: width of the page, in characters
# start_word: index of the first word to start the page with
# min_width: minimum line width; if moving a word to the next line would make the current line less than this, then the word will be broken up and hyphenated instead
# max_lines: height of the page, in lines
# start_indent: initial indent level to start at; should pass in the 4th value returned by the previous page's call
# Returns a 3-tuple of the formatted page, the number of lines that were put onto the page, the index (in <words>) of the next word after the end of the page, and the indent level left off at (so that in-paragraph indent will persist when the paragraph is split between pages)
	out_text = ''
	total_width = 0
	this_line = []
	n_lines = 0
	new_para = True
	i = start_word
	indent = start_indent
	width_with_indent = width-indent
	indent_spaces = ' '*indent
	words[i] = ' '*(start_indent*indent_in//indent_out)+words[i]  # If we have a starting indent from the previous call, we add 'fake' indent spaces to the first word, which will then be caught by the new_para code
	while i < len(words):
		word = words[i]
		if not word:	# A 'blank' word indicates multiple consective spaces in the input. Ignore.
			i += 1
			continue
		if new_para: # Start of a new paragraph; check if this paragraph has an indent and set variables accordingly
			words[i], indent = get_word_and_indent(words[i])
			if words[i]:
				word = words[i]
			width_with_indent = width-indent
			indent_spaces = ' '*indent
			new_para = False
		new_total_width = total_width + len(word)+1
		if new_total_width <= width_with_indent:	# Adding this word to the line won't put it over the column width, so just add it
			this_line += [word]
			total_width = new_total_width
			if word[-1] == '\n':	# This is the last word in the paragraph so deal with that
				n_lines += 1
				out_text += indent_spaces+justify_line(this_line, total_width-len(this_line), width_with_indent)
				if max_lines and n_lines > max_lines-1:
					return (out_text, n_lines, i+1, 0)
				total_width = 0
				this_line = []
				new_para = True
		else:	# Adding this word would put it over the column width; start a new line 
			n_lines += 1
			if max_lines and n_lines > max_lines-1:
				jl = indent_spaces+justify_line(this_line, total_width-len(this_line), width_with_indent)
				out_text += jl
				return (out_text, n_lines, i, indent)
			if(total_width < (min_width or 1)):	# We need to break this word up with a hyphen
				firsthalf = word[:width_with_indent-2-total_width]
				rest = word[width_with_indent-2-total_width:]
				this_line += [firsthalf+'-']
				total_width = width_with_indent
				#words.insert(i+1, rest)
				words[i] = rest
			i -= 1
			jl = indent_spaces+justify_line(this_line, total_width-len(this_line), width_with_indent)
			out_text += jl
			total_width = 0
			this_line = []
		i+=1
	out_text += indent_spaces+justify_line(this_line, total_width-len(this_line), width_with_indent)
	return (out_text, n_lines, i, indent)
