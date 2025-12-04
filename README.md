# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/andgineer/goodreads-export/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                        |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------- | -------: | -------: | ------: | --------: |
| src/goodreads\_export/author\_file.py       |       43 |        7 |     84% |     80-86 |
| src/goodreads\_export/authored\_file.py     |       15 |        0 |    100% |           |
| src/goodreads\_export/book\_file.py         |       56 |        1 |     98% |        99 |
| src/goodreads\_export/clean\_file\_name.py  |        5 |        0 |    100% |           |
| src/goodreads\_export/data\_file.py         |       61 |        6 |     90% |42, 46, 77, 126-130 |
| src/goodreads\_export/goodreads\_book.py    |       36 |        0 |    100% |           |
| src/goodreads\_export/library.py            |      173 |        9 |     95% |27, 263-265, 267-270, 296, 304, 327 |
| src/goodreads\_export/log.py                |       65 |        7 |     89% |97-100, 111, 123, 130 |
| src/goodreads\_export/main.py               |      248 |       28 |     89% |141, 143, 180-181, 191, 242-243, 250, 388-392, 397, 406-408, 424-429, 525-528, 562-564, 638 |
| src/goodreads\_export/series\_file.py       |       36 |        4 |     89% | 47, 74-80 |
| src/goodreads\_export/stat.py               |       13 |        0 |    100% |           |
| src/goodreads\_export/template\_metadata.py |       46 |        8 |     83% |     80-98 |
| src/goodreads\_export/templates.py          |      116 |       13 |     89% |15-16, 21, 26-27, 155-156, 178, 230, 250, 269, 275, 282 |
| src/goodreads\_export/version.py            |        1 |        0 |    100% |           |
|                                   **TOTAL** |  **914** |   **83** | **91%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/andgineer/goodreads-export/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/andgineer/goodreads-export/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/andgineer/goodreads-export/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/andgineer/goodreads-export/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fandgineer%2Fgoodreads-export%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/andgineer/goodreads-export/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.