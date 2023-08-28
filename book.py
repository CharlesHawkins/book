#!/usr/bin/env python3

import curses
import argparse as ap
import re
import sys
from os import path

from libjust import *

try:
	import pyperclip
	paste = True
except ImportError:
	paste = False

try:
	import procname
	procname.setprocname('book')
except ImportError:
	pass

epub = True
ebl = True
bs = True
try:
	import ebooklib
	from ebooklib import epub
except ImportError:
	epub = False
	ebl = False
try:
	import bs4
except ImportError:
	epub = False
	bs = False

# Key constants
uparrows = [curses.KEY_UP, ord('k')]
downarrows = [curses.KEY_DOWN, ord('j')]
leftarrows = [curses.KEY_LEFT, ord('h')]
rightarrows = [curses.KEY_RIGHT, ord('l')]

nextpage = rightarrows + downarrows
prevpage = leftarrows + uparrows

esc = 0x1B
esc_char = chr(esc)

par = ap.ArgumentParser(description = 'Terminal ebook reader')
par.add_argument('i', nargs='?', help = 'File to read from')
par.add_argument('-e', '--epub', action = 'store_true', help = 'Read the specified file as an epub book', dest = 'e')
par.add_argument('-m', '--merge-lines', action = 'store_true', help = 'Merge lines separated by only a single newline', dest = 'm')
par.add_argument('-c', '--cols', type=int, default=2, help = 'Number of columns to display', dest = 'c')
par.add_argument('-p', '--clipboard', action = 'store_true', help = 'Get input from clipboard instead of file', dest = 'p')
par.add_argument('-u', '--mouse', action = 'store_true', help = 'Enable mouse support', dest = 'u')
par.add_argument('-n', '--no-warn', action = 'store_true', help = 'Do not warn before quitting if the current read position is unsaved', dest = 'n')
par.add_argument('-v', '--verbose', action = 'store_true', help = 'Print extra info to the status line', dest = 'v')

args = par.parse_args()

re_linebreak = re.compile('(?<!\n)\n(?!\n)')
re_word = re.compile('[^ ]+')

global text

if args.p:
	if not paste:
		sys.stderr.write('Input from clipboard requires the pyperclip module\n')
		exit(1)
	text = pyperclip.paste().lstrip(' \r\n').strip()
	save = False
elif args.i is None or args.i == '-':
	infile = sys.stdin
	save = False
else:
	try:
		infilename = path.abspath(args.i)
		savename = '%s/.%s.cbookmark'%(path.dirname(infilename),path.basename(infilename))
		save = True
		if args.e:
			if not epub:
				if not ebl:
					sys.stderr.write('Reading epub requires the ebooklib python module (https://pypi.org/project/EbookLib/)\n')
				if not bs:
					sys.stderr.write('Reading epub requires the BeautifulSoup4 python module (https://pypi.org/project/beautifulsoup4/)\n')
				exit(1)
			infile = epub.read_epub(args.i, options={'ignore_ncx':True})
			text = ''
			for item in infile.get_items_of_type(ebooklib.ITEM_DOCUMENT):
				text += bs4.BeautifulSoup(item.get_body_content(), features='lxml').text.rstrip() + '\n\n'
		else:
			infile = open(args.i, 'r')
			text = infile.read()
	except IOError as e:
		sys.stderr.write('Error: Could not open input file %s: %s\n'%(args.i, e.strerror))
		exit(1)


def create_column_layout(screen, cols, margin, top, bottom):
	(y, x) = screen.getmaxyx()
	page_wins = [None]*cols
	page_n_wins = [None]*cols
	page_width = (x-margin*(cols+1))//cols
	page_height = y-top-bottom
	page_n_width = page_width//2
	status_win = screen.derwin(1, x-2*margin, y-2, margin)
	for i in range(cols):
		page_wins[i] = screen.derwin(page_height, page_width, top, margin+i*(page_width+margin))
		page_n_wins[i] = screen.derwin(1, page_n_width, y-2, margin+i*(page_width+margin)+page_n_width)
	return page_wins, page_n_wins, status_win, page_width-1, page_height-1

def display_page(win, pages, page):
	(y, x) = win.getmaxyx()

def status(str, win):
	(y, x) = win.getmaxyx()
	win.addstr(0,0,str[:x-1])
	win.refresh()

def get_progress_bar(page, pages, win, cols):
	(y, x) = win.getmaxyx()
	x -= 1
	pct = page/(pages-(pages%cols))
	pct_str = str(round(pct*100,2))+'%'
	x_left = x - len(pct_str)
	done = int(pct*x_left)
	left = x_left-done
	return '#'*done+'-'*left+pct_str

def ready_text(text, page_width, page_height):
	if args.m:
		text = re_linebreak.sub(' ', text)
	if text[-1] != '\n': text += '\n'
	words = split_text_into_words(text)
	pages, index = split_words_into_pages(words, page_width, page_height, 1)
	return pages, index

def highlight_word(word, page_text, page_win):
	lines = page_text.split('\n')
	word_count = 0
	word_pos = None
	word_text = ''
	for l in range(len(lines)):
		words = re_word.findall(lines[l])
		new_word_count = word_count + len(words)+1
		if(new_word_count > word):
			word_match = words[word-word_count]
			word_text = word_match.group(0)
			word_pos = word_match.start(0)
			page_win.addstr(l, word_pos, word_text, curses.A_REVERSE)
			page_win.refresh()
			return
		else:
			word_count = new_word_count

def highlight_line(line, page_text, page_win):
	line_text=page_text.split('\n')[line]
	page_win.addstr(line, 0, line_text, curses.A_REVERSE)
	page_win.refresh()

def first_word_of_line(line, page_text):
	lines = page_text.split('\n')
	word = 0
	for line_n in range(min(line, len(lines))):
		line_text = lines[line_n]
		line_text = line_text.rstrip()
		if not line_text:
			word += 1
		else:
			line_words = re_word.findall(line_text)
			word += len(line_words)
	return word

def is_win_big_enough(y, x, cols, margin, top, bottom):
	page_width = (x-margin*(cols+1))//cols
	page_height = y-top-bottom
	return page_width > 7 and page_height > 0

def set_mouse_mode(mode):
	sys.stdout.write(f'{esc_char}[?9{"h" if mode else "l"}')

def find_clicked_line(x, y, top, margin, page_width, n_pages, win_height):
	y -= top
	y = min(y, win_height-2)
	x -= margin
	page = min(max(0, x // (page_width+margin+1)), n_pages-1)
	return page, y
curses_mouse_states = {
    curses.BUTTON1_PRESSED: 'Button 1 Pressed', 
    curses.BUTTON1_RELEASED: 'Button 1 Released', 
    curses.BUTTON1_CLICKED: 'Button 1 Clicked',
    curses.BUTTON1_DOUBLE_CLICKED: 'Button 1 Double-Clicked',
    curses.BUTTON1_TRIPLE_CLICKED: 'Button 1 Triple-Clicked',

    curses.BUTTON2_PRESSED: 'Button 2 Pressed', 
    curses.BUTTON2_RELEASED: 'Button 2 Released', 
    curses.BUTTON2_CLICKED: 'Button 2 Clicked',
    curses.BUTTON2_DOUBLE_CLICKED: 'Button 2 Double-Clicked',
    curses.BUTTON2_TRIPLE_CLICKED: 'Button 2 Triple-Clicked',

    curses.BUTTON3_PRESSED: 'Button 3 Pressed', 
    curses.BUTTON3_RELEASED: 'Button 3 Released', 
    curses.BUTTON3_CLICKED: 'Button 3 Clicked',
    curses.BUTTON3_DOUBLE_CLICKED: 'Button 3 Double-Clicked',
    curses.BUTTON3_TRIPLE_CLICKED: 'Button 3 Triple-Clicked',

    curses.BUTTON4_PRESSED: 'Button 4 Pressed', 
    curses.BUTTON4_RELEASED: 'Button 4 Released', 
    curses.BUTTON4_CLICKED: 'Button 4 Clicked',
    curses.BUTTON4_DOUBLE_CLICKED: 'Button 4 Double-Clicked',
    curses.BUTTON4_TRIPLE_CLICKED: 'Button 4 Triple-Clicked',

    curses.BUTTON_SHIFT: 'Button Shift', 
    curses.BUTTON_CTRL: 'Button Ctrl', 
    curses.BUTTON_ALT: 'Button Alt'
}

margin = 3
top = 1
bottom = 2
def main(screen):
	global text
	curses.use_default_colors()
	curses.curs_set(False)
	screen.refresh()
	(y, x) = screen.getmaxyx()
	cols = args.c
	page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, margin, top, bottom)
	page = 0
	(pages, index) = ready_text(text, page_width, page_height)
	status_text = None
	def save_bookmark(word):
		bkmkfile = open(savename, 'w')
		bkmkfile.write(str(word))
		saved_word = word
		bkmkfile.close()

	if save:
		try:
			bkmkfile = open(savename, 'r')
			word = int(bkmkfile.read())
			page = find_page_with_word(word, index)
			page = (page//cols)*cols
		except Exception as e:
			word = index[page-1] if page > 0 else 0
		saved_word = word
	else:
		word = 0
	if args.u:
		curses.mousemask(curses.ALL_MOUSE_EVENTS)

	hl_page = None
	hl_line = None

	while True:
		screen.clear()
		for i in range(cols):
			if page+i < len(pages):
				if not curses.is_term_resized(y, x):
					page_wins[i].addstr(0,0,pages[page+i])
					if not status_text:
						page_n_wins[i].addstr(0,0,str(page+i+1))
					page_wins[i].refresh()
					page_n_wins[i].refresh()
				#highlight_word(1, pages[page+i], page_wins[i])
		if status_text:
			status(status_text, status_win)
			status_text = None
		if hl_line is not None:
			highlight_line(hl_line, pages[page+hl_page], page_wins[hl_page])
			hl_line = None
		k = screen.getch()
		if k == curses.KEY_MOUSE:
			try:
				mouse_id, mouse_x, mouse_y, mouse_z, state = curses.getmouse()
				if state & curses.BUTTON1_CLICKED:
					mouse_page_rel, mouse_line = find_clicked_line(mouse_x, mouse_y, top, margin, page_width, len(page_wins), page_wins[0].getmaxyx()[0])
					mouse_page = page + mouse_page_rel
					word = (index[mouse_page-1] if mouse_page > 0 else 0) + first_word_of_line(mouse_line, pages[mouse_page])
					hl_line = mouse_line
					hl_page = mouse_page_rel
					if args.v:
						status_text = f'Click ({mouse_x}, {mouse_y}, {state}): Page {mouse_page+1}, Line {mouse_line+1} / {page_wins[0].getmaxyx()[0]}, word {word}'
					continue
				elif state & 2097512: # BUTTON5_PRESSED; sometimes the constant is unavailable
					k = ord('j')
				elif state & curses.BUTTON4_PRESSED:
					k = ord('k')
				if args.v:
					status_text = f'Click ({mouse_x}, {mouse_y}, {state})'
			except curses.error:
				continue
		if k == ord('q'):
			if (not args.n) and save and (saved_word != word):
				status_text=('Save new read position before quitting? (Y/N)')
				status(status_text, status_win)
				while True:
					k = screen.getch()
					if k == ord('y') or k == ord('Y'):
						try:
							save_bookmark(word)
							exit(0)
						except IOError as e:
							status_text = '%s: %s'%(savename, e.strerror)
					elif k == ord('n') or k == ord('N'):
						exit(0)
					else:
						status_text = 'Quit cancelled'
						break
			else:
				exit(0)
		elif k in nextpage:
			if page+cols < len(pages):
				page += cols
				word = index[page-1] if page > 0 else 0
		elif k in prevpage:
			if page >= cols:
				page -= cols
				word = index[page-1] if page > 0 else 0
		elif k == ord('=') or k == ord('+'):
			if is_win_big_enough(y, x, cols, margin, top, bottom):
				cols += 1
				page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, margin, top, bottom)
				(pages, index) = ready_text(text, page_width, page_height)
				page = find_page_with_word(word, index)
				page = (page//cols)*cols
			status_text = '%s column%s'%(cols,'' if cols == 1 else 's')
		elif k == ord('-') or k == ord('_'):
			if cols > 1:
				cols -= 1
				page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, margin, top, bottom)
				(pages, index) = ready_text(text, page_width, page_height)
				page = find_page_with_word(word, index)
				page = (page//cols)*cols
			status_text = '%s column%s'%(cols,'' if cols == 1 else 's')
		elif k == ord('S'):
			if save:
				try:
					save_bookmark(word)
					status_text = 'Saved'
					if args.v:
						status_text += f' (word #{word})'
				except IOError as e:
					status_text = '%s: %s'%(savename, e.strerror)
			else:
				status_text = 'Input not from file, save not available'
		elif k == ord('p'):
			status_text = get_progress_bar(page, len(pages), status_win, cols)
			status(status_text, status_win)
			screen.getch()
			status_text = None
		elif k == ord('P') or k == 0x10:  # 0x10 = Ctrl-p
			if not paste:
				status_text = 'Pasting from clipboard requires the pyperclip module'
			elif save:
				status_text = 'Input was from a file, cannot paste'
			else:
				pasted = pyperclip.paste().lstrip(' \r\n').rstrip()
				if not pasted:
					status_text = 'No text on clipboard'
				else:
					if k == 0x10:
						text = pasted
						status_text = 'Pasted (replacing)'
						page = 0
					else:
						text = text.lstrip(' \r\n').rstrip() + ('\n\n' if args.m else '\n') + pasted
						status_text = 'Pasted (appending)'
					(pages, index) = ready_text(text, page_width, page_height)
		elif k == curses.KEY_RESIZE:
			oldpage = page
			page_wins, page_n_wins, status_win, page_width, page_height = create_column_layout(screen, cols, 3, 1, 2)
			(pages, index) = ready_text(text, page_width, page_height)
			page = find_page_with_word(word, index)
			page = (page//cols)*cols
			#t = "%s, %s (%s)"%(y, x, curses.is_term_resized(y,x))
			(y, x) = screen.getmaxyx()
			#status_text = "%s -> %s, %s (%s)"%(t, y, x, curses.is_term_resized(y,x))

		elif args.v:
			status_text = str(k)

curses.wrapper(main)
set_mouse_mode(False)
