# Goodreads export to markdown files

Export your goodreads book reviews into markdown files.
With links to author files.

In review files there are also links to the goodread book page and
[Calibre](https://calibre-ebook.com/) URL to search
for this book in your local Calibre collection.

And some tags created from goodreads `shelves`.

This is how that looks like in [Obsidian](https://obsidian.md/):

![goodreads.png](goodreads.png)
![goodreads-author.png](goodreads-author.png)

### Installation

    pip install goodreads-export

It will install Linux or Windows script `goodreads-export`.

### How to create goodread export file

This application use CSV file created on goodreads.com.
How to create goodreads export see in https://www.goodreads.com/review/import

In 2022 they declared it to be removed by August, but at least at the end of 2022 it still works.

### Usage

    $> goodreads-export --help

    Usage: goodreads-export [OPTIONS] [CSV_FILE]

      Convert reviews and authors from goodreads export CSV file to markdown
      files.

      For example you can create nice structure in Obsidian.

      How to create goodreads export see in
      https://www.goodreads.com/review/import In 2022 they declare it to be
      removed by August, but at least at the end of 2022 it still works.

      CSV_FILE: Goodreads export file. By default `goodreads_library_export.csv`.

    Options:
      -o, --out PATH  Folder where we put result. By default current folder.
      --help          Show this message and exit.

If we run in the folder with goodreads export file (goodreads_library_export.csv) the
script without parameters, like that

    goodreads-export

It will create in this folder subfolders `reviws`, `toread`, `authors` with the md-files.
If you copy them into Obsidian vault, the files will be inside your Obsidian knowledgebase.

# source code

[sorokin.engineer/aios3](https://github.com/andgineer/goodreads-export)
