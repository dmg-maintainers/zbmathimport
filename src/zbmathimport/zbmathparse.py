import os
from datetime import datetime, UTC
from pathlib import Path
import json
import arxiv2bib
from doi2bib.crossref import get_bib_from_doi


from academic.generate_markdown import GenerateMarkdown


PUB_TYPES_ZBLATT_TO_CSL = {
  'j': 'article-journal',   # Journal Article
  'p': 'article',           # Preprint
  'a': 'chapter',           # Book Chapter
  's': 'paper-conference',  # Conference Paper
}


def save_bib_from_doi(bundle_path, doi, dry_run=False):
    """Save citation file from a given doi."""
    cite_path = os.path.join(bundle_path, "cite.bib")
    success, db = get_bib_from_doi(doi)
    if success and not dry_run:
        with open(cite_path, "w", encoding="utf-8") as f:
            f.write(db)
            return True
    return False


def save_bib_from_arxiv(bundle_path, doi, dry_run=False):
    """Save citation file from a given arxiv id."""
    # We don't do anything here, to stay on the safe
    # side of arxiv's policy towards crawling.
    # https://info.arxiv.org/help/robots.html
    return False


def parse_zblatt_document(
    entry,
    author_ids={},
    pub_dir=os.path.join("content", "publication"),
    featured=False,
    overwrite=False,
    compact=False,
    dry_run=False,
):
    """Parse a zblatt json document entry and generate corresponding publication bundle"""
    from academic.cli import log

    log.info(f"Parsing entry {entry['id']}")

    bundle_path = os.path.join(pub_dir, str(entry["id"]))
    markdown_path = os.path.join(bundle_path, "index.md")
    date = datetime.now(UTC)
    timestamp = date.isoformat("T") # RFC 3339 timestamp.

    # Prepare YAML front matter for Markdown file.
    if not dry_run:
        if overwrite or not os.path.isdir(bundle_path):
            from importlib import resources as import_resources
            # Create bundle dir.
            log.info(f"Creating folder {bundle_path}")
            if not dry_run:
                Path(bundle_path).mkdir(parents=True, exist_ok=True)


            # Load the Markdown template from within the `templates` folder of the `academic` package
            template = import_resources.read_text("academic.templates", "publication.md")

            with open(markdown_path, "w") as f:
                f.write(template)

    page = GenerateMarkdown(Path(bundle_path), dry_run=dry_run, compact=compact)
    page.load(Path("index.md"))

    # Decide whether we overwrite the entry.
    # We will do it if:
    # - the overwrite option is selected.
    # - The zbmath datestamp has changed.
    # - The entry type has changed. 
    datestamp =  entry['datestamp']
    default_csl_type = "manuscript"
    pub_type = PUB_TYPES_ZBLATT_TO_CSL.get(entry["document_type"]["code"], default_csl_type)
    if not overwrite:
        overwrite = 'zbmath_date' not in page.yaml or page.yaml['zbmath_date'] != datestamp
        overwrite = overwrite or ("publication_types" in page.yaml and page.yaml["publication_types"] == pub_type)
    # Do not overwrite publication bundle if it already exists.
    if not overwrite:
        log.warning(f"Skipping creation of {bundle_path} as it already exists. " f"To overwrite, add the `--overwrite` argument.")
        return

    page.yaml["zbmath_date"] = entry['datestamp']

    page.yaml["title"] = entry["title"]["title"]

    if entry['title'] is not None:
        page.yaml["subtitle"] = entry["title"]["subtitle"]

    year, month, day = "", "01", "01"
    if entry['year'] is not None:
        year = entry["year"]
    if len(year) == 0:
        log.error(f'Invalid date for entry `{entry["ID"]}`.')

    page.yaml["date"] = f"{year}-{month}-{day}"
    page.yaml["publishDate"] = timestamp # We could potentially use zblatt's datestamp

    authors = [author_ids.get(author["codes"][0], author["name"]) for author in  entry['contributors']['authors']]
    page.yaml["authors"] = authors
    #elif "editor" in entry:
    #    authors = entry["editor"]


    # Convert Bibtex publication type to the universal CSL standard, defaulting to `manuscript`
    page.yaml["publication_types"] = [pub_type]

    page.yaml["abstract"] = ""
    for contribution in  entry['editorial_contributions']:
      if contribution['contribution_type'] == 'summary' and contribution['reviewer']['reviewer_id'] is None:
        if contribution['text'] != "zbMATH Open Web Interface contents unavailable due to conflicting licenses.":
          page.yaml["abstract"] = contribution['text' ]

    page.yaml["featured"] = featured

    # Publication name.
    # This field is Markdown formatted, wrapping the publication name in `*` for italics
    source = entry['source']['series']
    publication = ""
    if "title" in source:
      publication = "*" + source['title'] + "*"
    page.yaml["publication"] = publication

    page.yaml["tags"] = entry["keywords"]

    links = [{"name": "zbmath", "url":entry['zbmath_url'], "id": entry["id"]}]
    createcitefile = True
    for link in entry["links"]:
      if link["type"] == "doi":
        doi = link["url"]
        page.yaml["doi"] =  doi
        if save_bib_from_doi(bundle_path, doi, dry_run):
            createcitefile = False
      else:
        links += [{"name": link["type"], "url": link["url"], "id": link["identifier"]}]
        if link["type"] == "arxiv" and createcitefile:
          save_bib_from_arxiv(bundle_path, link["identifier"], dry_run)
    if links:
        page.yaml["links"] = links

    # Save Markdown file.
    try:
        log.info(f"Saving Markdown to '{markdown_path}'")
        if not dry_run:
            page.dump()
    except IOError:
        log.error("Could not save file.")
    return page


def import_zblatt(
    json_database,
    author_ids={},
    pub_dir=os.path.join("content", "publication"),
    featured=False,
    overwrite=False,
    compact=False,
    dry_run=False,
):
    for entry in json_database:
      parse_zblatt_document(
            entry,
            author_ids=author_ids,
            pub_dir=pub_dir,
            featured=featured,
            overwrite=overwrite,
            compact=compact,
            dry_run=dry_run,
        )

