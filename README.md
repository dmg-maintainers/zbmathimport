# Import projects from zbmaths

This is an extension of the [academic](https://github.com/GetRD/academic-file-converter) project, to retrieve publication data from the [zbMath](zbmath.org) repository for a list of authors and generate publication data compatible with static website generators such as [Hugo](https://gohugo.io/).

## Usage

You can call this command as follows:
```
zbmathimport -c [authors.yml] -o [content/publication]
```

The file `authors.yml` should contain a list of zbmath author ids. These ids are used to generate a query to the zbmath API, and you may get an error, or an empty list of publications, if the list is incorrect.

If the `-c` option is omitted, the command will look for a `author.yml` inside the folder. If the `-o` option is omitted, it will generate the markdown files in the `content/publication` folder.

```
[author.yml]
- first.author
- second.author
- ...

```

## Limitations

- Currently only the publication of the current year are queried.
- No bibtex entry is generated.
- When abstracts are unavailable on zbmath due to license incompatibilities, no abstract is written.
- Some bibliographic data (page numbers, journal issue, volume) is not recorded.
