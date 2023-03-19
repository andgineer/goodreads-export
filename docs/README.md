# Goodreads export to markdown files

Export your goodreads book reviews into markdown files.
Also creates author markdown files connected to the review.

In review files there are also links to the goodreads' book page and
[Calibre](https://calibre-ebook.com/) URL to search
for this book in your local Calibre collection.

The application add tags based on your `shelves`.

This is how that looks like in [Obsidian](https://obsidian.md/):

![goodreads.png](goodreads.png)
![goodreads-author.png](goodreads-author.png)

### How to create goodreads export file

This application use CSV file created on goodreads.com.
How to create goodreads export see in https://www.goodreads.com/review/import

In 2022 they declared the export feature to be removed by August 2020, but at least at the beginning of
2023 it still works.

In fact I created the application as one-time solution to go away from goodreads with
my 600-something book reviews. But as it still works now I use it also to incrementally update my
markdown files in Obsidian.

### Why this lame approach with manually exported file

Goodreads at 2020 had stopped giving out API keys.

So it's all about making lemonade out of lemons.

I cannot not use the API to fully automate the process,
but at least I can still get my data from goodreads.

Unfortunately with this manual export step included.

### Incremental updates

Application can add reviews to already existed files.

It reads files from the folders and won't create reviews that are already there.
This is possible because there are goodreads book ID in the markdown files - inside link to goodreads.

So even if you rename the file the application still know what book it is about thanks to the
goodreads link inside the file. This links created by the application and all you have to do
just do not delete or modify them.

#### Author files

Unfortunately there are no author ID in the goodreads export file.

Despite that the application add to author files link for search on goodreads, with the author
name inside the link.

So if you just rename the file, application still will know the original
author name from the link.
Of cause you should not delete or modify the link.

Author name is always get from the link and not from the author file name.

#### Merging different author names

In goodreads could be a lot of different spellings of the author name plus versions in
different languages.

With this application you can merge them so you will have one list of all author book.

For that all author name versions should be listed as links in one author file -
just copy them from other author files to that `primary` author file.
First link should contain `primary` name.

Application will relink all existed and newly created books with other author names
in this file to this `primary` name.

If you need only this re-link without importing goodreads file use option `--merge`.

#### Templates

The application use templates that you can modify.
Use `init` command to copy built-in templates to some folder and modify them.

### Installation

    pip install goodreads-export

It will install Linux or Windows script `goodreads-export`.

### Usage

    $> goodreads-export --help

    Usage: goodreads-export [OPTIONS] COMMAND [ARGS]...

      Create md-files from https://www.goodreads.com/ CSV export.

      For example, you can create nice structure in Obsidian.

      How to create goodreads export see in
      https://www.goodreads.com/review/import

      They declare it to be removed by August 2022, but at least in the 2023 it
      still works.

      Documentation https://andgineer.github.io/goodreads-export/

      To see help on the commands use `goodreads-export COMMAND --help`. For
      example: `goodreads-export import --help`.

    Options:
      --version  Show version.
      --help     Show this message and exit.

    Commands:
      check   Check templates consistency with extraction regexes.
      import  Convert goodreads export CSV file to markdown files.
      init    Create templates folder in path from `--templates-folder`.
      merge   Merge authors in the `BOOKS_FOLDER`.

    $> goodreads-export import --help

    Usage: goodreads-export import [OPTIONS] BOOKS_FOLDER

      Convert goodreads export CSV file to markdown files.

      BOOKS_FOLDER Folder where we put result. Do not change existed files except
      authors merge if necessary.

      See details in https://andgineer.github.io/goodreads-export/

    Options:
      -v, --verbose                Increase verbosity.
      -t, --templates-folder PATH  Folder with templates. If not absolute it's
                                   relative to `BOOKS_FOLDER`. If not specified,
                                   look for `./templates` in `BOOKS_FOLDER`. If
                                   not found use built-in templates, see
                                   `--builtin-name`.
      -b, --builtin-name TEXT      Name of the built-in template. Use `default` if
                                   not specified.
      -i, --in TEXT                Goodreads export file. By default
                                   `goodreads_library_export.csv`. if you specify
                                   just folder it will look for file with this
                                   name in that folder.
      --help                       Show this message and exit.

If we run in the folder with goodreads export file (goodreads_library_export.csv) the
script without parameters, like that

    goodreads-export import .

It will create in this folder subfolders `reviws`, `toread`, `authors` with the md-files.
Alternatively you can specify direct path inside Obsidian vault with your books folder
and the application will update it.

# source code

[sorokin.engineer/aios3](https://github.com/andgineer/goodreads-export)
