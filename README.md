### Book
Book is a terminal-based ebook reader that renders a book in a multi-column layout with margins, page numbers, and justified text. It is still a work in progress but in its current form it supports plain-text (.txt) and epub ebooks (such as can be downloaded off Project Gutenberg) and bookmarks to save your place.

#### Command-line options
The basic way of invoking it is:

	book.py ebook.txt

Several options are available:
* -e or --epub will interpret the specified book as being in epub format. This requires the Python modules [ebooklib](https://pypi.org/project/EbookLib/) and [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/). Epub support is currently very rudimentary and just extracts the plain-text of the whole book, with no special recognition of chapters, footnotes, formatting, or anything else.
* -m or --merge-lines will remove single newlines, but keep sequences of two or more newlines. This is useful for ebooks that have the soft newlines within each paragraph already "baked in", as is the case with Gutenberg's plain-text ebooks.
* -c or --cols is used to set the number of columns. The default is 2.
* -p or --clipboard is used to read text from the system clipboard instead of a file. This requires the [pyperclip](https://pypi.org/project/pyperclip/)  Python module.
* -n or --no-warn suppresses the "Save position before quitting?" confirmation that is otherwise given before quitting if the read position has changed since the last save.
* -u or --mouse enables mouse support (mouse is enabled by default, but -u can be used to override an earlier --no-mouse)
* --no-mouse disables all mouse support.

#### Usage and keys
* You can page forward and backward with the arrows (up/down and left-right both work), or with the vim keys h, j, k, and l (h and k go back a page, j and l go forward).
* Press p for a progress bar along the bottom, representing your progress through the book. Press any key to dismiss it.
* Press shift-s to save your progress. This creates a file called (if your book is Book.txt) .Book.txt.cbookmark that contains the word number from the upper-left of the screen. If Book is run again later on the same file it will find the bookmark and go to the page that contains that word. Given that terminal windows differ in size, it may not be in the same place as it was when you saved, but doing it this way at least garauntees that it won't have gone past wherever you were reading. Note that the bookmark file has .cbookmark at the end, while the files from my other reader program, [Oneline](https://github.com/CharlesHawkins/oneline), have .bookmark, and thus they will be separate bookmarks if you view the same book with both programs. This is because Oneline saves your position by line and Book saves by word.
* Press q to quit Book. If your read position has moved since the last time you saved your place, it will ask if you want to save it again. Press Y to save and quit, N to quit without saving, anything else to cancel and return to the book. Run book.py with -n to suppress this confirmation.
* Press shift-p to paste text from the system clipboard, appending to the end of the current document. This only works if you were reading text from the clipboard in the first place with -p, or text piped in from stdin. If you instead press ctrl-p, the clipboard contents replace the current text rather than being appended to the end. Pasting form the clipboard requires the [pyperclip](https://pypi.org/project/pyperclip/) Python module.
* Press + and - to increase or decrease the number of columns
* When mouse mode is enabled, you can do the following:
    * Left-click in the left third of the screen to go back a page, or in the right third of the screen to go forward a page
    * Right-click a line to set the first word on that line as your current reading place; turning pages will reset the reading place to the upper-leftmost word on the screen. The reading place has the following effects: 
        * The save command (Shift-S) will save to your current reading place
        * When resizing the terminal window or changing the number of columns your reading place will be kept on screen
    * Scroll the mouse wheel down or up to go forward or back a page
