{clean_file_name(self.author)} - {clean_file_name(self.title)}.md

[[{clean_file_name(self.author)}]]: [{self.title}]({book_url})
ISBN{self.isbn} (ISBN13{self.isbn13})
{' '.join(['[[' + self.series_full_name(series) + ']]' for series in self.series])}
{self.review}

[Search in Calibre](calibre://search/_?q={urllib.parse.quote(self.title)})

{" ".join(self.tags)}
