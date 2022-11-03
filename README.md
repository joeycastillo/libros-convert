# libros-convert

A tool to convert epubs for the Open Book's [Libros](https://github.com/joeycastillo/libros) firmware.

**THIS IS NOT READY YET.** It is provided for folks who want to hack along on the Open Book at home, but it's very early stage software, can easily fail on a variety of different inputs, and generally shouldn't be trusted. With that said, I've had very good results converting EPUBs from [Standard Ebooks](https://standardebooks.org).

## Getting Started

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt 
python3 convert.py louisa-may-alcott_little-women.epub
```

The script itself is an interactive utility; you can toggle chapters on and off before exporting the final text file.

More to come.
