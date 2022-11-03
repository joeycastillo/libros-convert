import io
import sys
from epub2txt import epub2txt
from lxml.etree import XMLSyntaxError

# Designed for use with Standard Ebooks EPUB files.
# May work with others, but their structure is excellent.
try:
    filepath = sys.argv[1]
except:
    print('usage: python3 convert.py book_to_convert.epub')
    print('make sure to have a folder named "output" alongside this script')
    exit()

try:
    chapters = epub2txt(filepath, clean = True, outputlist = True, debug = False, do_formatting=True)
except XMLSyntaxError:
    print("\033[1mWARNING: Unable to parse text formatting! Book will not have bold or italic type.\033[0m")
    chapters = epub2txt(filepath, clean = True, outputlist = True, debug = False, do_formatting=False)

title = None
author = None
language = None
genre = None
description = None

for group in epub2txt.metadata:
    for item in group:
        if item == 'title':
            title = group[item][0][0]
        if item == 'creator':
            author = group[item][0][0]
        if item == 'language':
            language = group[item][0][0][0:2]
        if item == 'subject':
            genre = group[item][0][0]
        # if item == 'description':
        #     description = group[item][0][0].replace('\n', ' ')
        # print(item, ' : ', end = '')
        # if group[item][0][0] is not None:
        #     print(group[item][0][0])
        # elif group[item][0][1]:
        #     print(group[item][0][1])

print()
print(f'Title: {title}')
print(f'Author: {author}')
print(f'Genre: {genre}')
print(f'Language: {language}')
print(f'Description: {description}')
print('\nChapters:')

done = False
chapters_selected = []
for i in range(0, len(epub2txt.spine)):
    if epub2txt.spine[i] in ['titlepage.xhtml', 'imprint.xhtml', 'colophon.xhtml', 'uncopyright.xhtml']:
        chapters_selected.append(False)
    else:
        chapters_selected.append(True)

while not done:
    for i in range(0, len(epub2txt.spine)):
        selected = '*' if chapters_selected[i] else ' '
        print(f'{i + 1:3}. [{selected}] {epub2txt.spine[i]}')
    i = input('Enter a chapter number to toggle its inclusion, or a blank line when finished: ')
    if i:
        chapters_selected[int(i) - 1] = not chapters_selected[int(i) - 1]
    else:
        done = True

components = filepath.split('.')
components[-1] = 'txt'
outfile = './output/' + '.'.join(components)

with io.open(outfile, 'w', encoding='utf8') as f:
    f.write(u'---\n')
    f.write(f'TITL: {title}\n')
    f.write(f'AUTH: {author}\n')
    f.write(f'DESC: {description}\n')
    f.write(f'GNRE: {genre}\n')
    f.write(f'LANG: {language}\n')
    f.write(u'---\n')
    for i in range(0, len(chapters)):
        if chapters_selected[i]:
            f.write(u'\u001e')
            # this is strange but standard ebooks seem to drop BOMs before unicode characters?
            f.write(''.join(chapters[i].split(u'\ufeff')))
            f.write(u'\n')
