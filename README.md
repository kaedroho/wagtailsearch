# Django ModelSearch

Django ModelSearch allows you index Django models and search using the ORM. It supports PostgreSQL FTS, SQLite FTS5, MySQL FTS, MariaDB FTS, and Elasticsearch.

Features:

- Indexing content with Elasticsearch and most of Django's database backends (with support for native FTS features)
- Search Elasticsearch with Django QuerySets
- Autocomplete
- Faceting
- Per-field boosting
- Fuzzy Search
- Phrase search
- Query combinators

This has been built into [Wagtail CMS](https://github.com/wagtail/wagtail) since 2014 and extracted into a separate package in March 2025.

## Installation

Install with PIP, then add to `INSTALLED_APPS` in your Django settings:

```shell
pip install modelsearch
```

```python
# settings.py

INSTALLED_APPS = [
    ...
    "modelsearch
    ...
]
```

Configure a backend in Django settings. For example, to configure Elasticsearch:

```python
# settings.py

MODELSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'modelsearch.backends.elasticsearch8',
        'URLS': ['https://localhost:9200'],
        'INDEX': 'wagtail',
        'TIMEOUT': 5,
        'OPTIONS': {},
        'INDEX_SETTINGS': {},
    }
}
```

## Indexing content

To index a model, add `modelsearch.index.Indexed` to the model class and define some `search_fields`:

```
from modelsearch import index

class Book(index.Indexed, models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255, choices=GENRE_CHOICES)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    published_date = models.DateTimeField()

    search_fields = [
        index.SearchField('title', boost=10),
        index.AutocompleteField('title', boost=10),
        index.SearchField('get_genre_display'),

        index.FilterField('genre'),
        index.FilterField('author'),
        index.FilterField('published_date'),
    ]
```

Then run the `rebuild_index` management command to build the search index.

## Searching content

Searching is done using a `.search()` method that is added to the querysets of indexed models.

For example:

```python
>>> Book.objects.filter(author=roald_dahl).search("chocolate factory")
[<Book: Charlie and the chocolate factory>]
```

Any fields that are used in `.filter()`, `.exclude()` or `.order_by()` must be indexed with `index.FilterField` so they are added to the Elasticsearch index. Filters are automatically rewritten as Elasticsearch DSL queries.
