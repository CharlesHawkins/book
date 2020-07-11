### Book
Book is a terminal-based ebook reader that renders a book in a multi-column layout with margins, page numbers, and justified text. It is not currently considered finished but in its current form it supports plain-text ebooks (such as can be downloaded off Project Gutenberg) and bookmarks to save your place.

#### Command-line options
The basic way of invoking it is:

	book.py ebook.txt

Several options are available:
* -m or --merge-lines will remove single newlines, but keep sequences of two or more newlines. This is useful for ebooks that have newlines already "baked in" for each line, as is the case with Gutenberg's plain-text ebooks.
* -c or --cols is used to set the number of columns. The default is 2.
* -p or --clipboard is used to read text from the system clipboard instead of a file. This requires the [pyperclip](https://pypi.org/project/pyperclip/)  Python module.

#### Usage and keys
* You can page forward and backward with the arrows (up/down and left-right both work), or with the vim keys h, j, k, and l (h and k go back a page, j and l go forward).
* Press p for a progress bar along the bottom, representing your progress through the book. Press any key to dismiss it.
* Press shift-s to save your progress. This creates a file called (if your book is Book.txt) .Book.txt.cbookmark that contains the word number from the upper-left of the screen. If Book is run again later on the same file it will find the bookmark and go to the page that contains that word. Given that terminal windows differ in size, it may not be in the same place as it was when you saved, but doing it this way at least garauntees that it won't have gone past wherever you were reading. Note that the bookmark file has .cbookmark at the end, while the files from my other reader program, [Oneline](https://github.com/CharlesHawkins/qed), have .bookmark, and thus they will be separate bookmarks if you view the same book with both programs. This is because Oneline saves your position by line and Book saves by word.
* Press q to quit book. Currently it does not ask you if you want to save your place.
* Press shift-p to paste text from the clipboard, appending to the end of the current document. This only works if you were reading from the clipboard in the first place with -p. If you instead press ctrl-p, the clipboard contents replace the current text rather than being appended to the end. Pasting form the clipboard requires the [pyperclip](https://pypi.org/project/pyperclip/) Python module.
* Press + and - to increase or decrease the number of columns
