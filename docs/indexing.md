(modelsearch_indexing)=

# Indexing

To make a model searchable, you'll need to add it to the search index. All pages, images, and documents are indexed for you, so you can start searching them right away.

If you have created some extra fields in a subclass of Page or Image, you may want to add these new fields to the search index too so that a user's search query will match their content. See {ref}`modelsearch_indexing_fields` for info on how to do this.

If you have a custom model that you would like to make searchable, see {ref}`modelsearch_indexing_models`.

(modelsearch_indexing_update)=

## Updating the index

If the search index is kept separate from the database (when using Elasticsearch for example), you need to keep them both in sync. There are two ways to do this: using the search signal handlers, or calling the `rebuild_modelsearch_index` command periodically. For the best speed and reliability, it's best to use both if possible.

### Signal handlers

`modelsearch` provides some signal handlers which bind to the save/delete signals of all indexed models. This would automatically add and delete them from all backends you have registered in `MODELSEARCH_BACKENDS`. These signal handlers are automatically registered when the `modelsearch` app is loaded.

In some cases, you may not want your content to be automatically reindexed and instead rely on the `rebuild_modelsearch_index` command for indexing. If you need to disable these signal handlers, use one of the following methods:

#### Disabling auto-update signal handlers for a model

You can disable the signal handlers for an individual model by adding `search_auto_update = False` as an attribute on the model class.

#### Disabling auto-update signal handlers for a search backend/whole site

You can disable the signal handlers for a whole search backend by setting the `AUTO_UPDATE` setting on the backend to `False`.

If all search backends have `AUTO_UPDATE` set to `False`, the signal handlers will be completely disabled for the whole site.

For documentation on the `AUTO_UPDATE` setting, see {ref}`modelsearch_backends_auto_update`.

### The `rebuild_modelsearch_index` command

Wagtail also provides a command for rebuilding the index from scratch.

`./manage.py rebuild_modelsearch_index`

It is recommended to run this command once a week and at the following times:

-   whenever any pages have been created through a script (after an import, for example)
-   whenever any changes have been made to models or search configuration

The search may not return any results while this command is running, so avoid running it at peak times.

(modelsearch_disable_indexing)=

### Disabling model indexing

Indexing of a model can be disabled completely by setting `search_fields = []` within the model. This will disable index updates by the signal handler and by the `rebuild_modelsearch_index` management command.

(modelsearch_indexing_fields)=

## Indexing extra fields

Fields must be explicitly added to the `search_fields` property of your `Page`-derived model, in order for you to be able to search/filter on them. This is done by overriding `search_fields` to append a list of extra `SearchField`/`FilterField` objects to it.

### Example

This creates an `EventPage` model with two fields: `description` and `date`. `description` is indexed as a `SearchField` and `date` is indexed as a `FilterField`.

```python
from modelsearch import index
from django.utils import timezone

class EventPage(Page):
    description = models.TextField()
    date = models.DateField()

    search_fields = Page.search_fields + [ # Inherit search_fields from Page
        index.SearchField('description'),
        index.FilterField('date'),
    ]


# Get future events which contain the string "Christmas" in the title or description
>>> EventPage.objects.filter(date__gt=timezone.now()).search("Christmas")
```

(modelsearch_index_searchfield)=

### `index.SearchField`

These are used for performing full-text searches on your models, usually for text fields.

#### Options

-   **boost** (`int/float`) - This allows you to set fields as being more important than others. Setting this to a high number on a field will cause pages with matches in that field to be ranked higher. By default, this is set to 2 on the Page title field and 1 on all other fields.

    ```{note}
    The PostgresSQL full-text search only supports [four weight levels (A, B, C, D)](https://www.postgresql.org/docs/current/textsearch-features.html).
    When the database search backend `modelsearch.backends.database` is used on a PostgreSQL database, it will take all boost values in the project into consideration and group them into the four available weights.

    This means that in this configuration there are effectively only four boost levels used for ranking the search results, even if more boost values have been used.

    You can find out roughly which boost thresholds map to which weight in PostgreSQL by starting a new Django shell with `./manage.py shell` and inspecting `modelsearch.backends.database.postgres.weights.BOOST_WEIGHTS`.
    You should see something like `[(10.0, 'A'), (7.166666666666666, 'B'), (4.333333333333333, 'C'), (1.5, 'D')]`.
    Boost values above each threshold will be treated with the respective weight.
    ```

-   **es_extra** (`dict`) - This field is to allow the developer to set or override any setting on the field in the Elasticsearch mapping. Use this if you want to make use of any Elasticsearch features that are not yet supported in Wagtail.

(modelsearch_index_autocompletefield)=

### `index.AutocompleteField`

These are used for autocomplete queries that match partial words. For example, a page titled `Hello World!` will be found if the user only types `Hel` into the search box.

This takes the same options as `index.SearchField`.

```{note}
`index.AutocompleteField` should only be used on fields that are displayed in the search results. This allows users to see any words that were partial-matched.
```

(modelsearch_index_filterfield)=

### `index.FilterField`

These are added to the search index but are not used for full-text searches. Instead, they allow you to run filters on your search results.

(modelsearch_index_relatedfields)=

### `index.RelatedFields`

This allows you to index fields from related objects. It works on all types of related fields, including their reverse accessors.

For example, if we have a book that has a `ForeignKey` to its author, we can nest the author's `name` field inside the book:

```python
from modelsearch import index

class Book(models.Model, index.Indexed):
    ...

    search_fields = [
        index.SearchField('title'),
        index.FilterField('published_date'),

        index.RelatedFields('author', [
            index.SearchField('name'),
        ]),
    ]
```

This will allow you to search for books by their author's name.

It works the other way around as well. You can index an author's books, allowing an author to be searched for by the titles of books they've published:

```python
from modelsearch import index

class Author(models.Model, index.Indexed):
    ...

    search_fields = [
        index.SearchField('name'),
        index.FilterField('date_of_birth'),

        index.RelatedFields('books', [
            index.SearchField('title'),
        ]),
    ]
```

#### Filtering on `index.RelatedFields`

It's not possible to filter on any `index.FilterFields` within `index.RelatedFields` using the `QuerySet` API. Placing `index.FilterField` inside `index.RelatedFields` is valid, and will cause the appropriate field data to be stored at indexing time, but the `QuerySet` API does not currently support filters that span relations, and so there is no way to access these fields. However, it should be possible to use them by querying Elasticsearch manually.

Filtering on `index.RelatedFields` with the `QuerySet` API is planned for a future release of Wagtail.

(modelsearch_indexing_callable_fields)=

### Indexing callables and other attributes

Search/filter fields do not need to be Django model fields. They can also be any method or attribute on your model class.

One use for this is indexing the `get_*_display` methods Django creates automatically for fields with choices.

```python
from modelsearch import index

class EventPage(Page):
    IS_PRIVATE_CHOICES = (
        (False, "Public"),
        (True, "Private"),
    )

    is_private = models.BooleanField(choices=IS_PRIVATE_CHOICES)

    search_fields = Page.search_fields + [
        # Index the human-readable string for searching.
        index.SearchField('get_is_private_display'),

        # Index the boolean value for filtering.
        index.FilterField('is_private'),
    ]
```

Callables also provide a way to index fields from related models. In the example from {ref}`inline_panels`, to index each BookPage by the titles of its related_links:

```python
class BookPage(Page):
    # ...
    def get_related_link_titles(self):
        # Get list of titles and concatenate them
        return '\n'.join(self.related_links.all().values_list('name', flat=True))

    search_fields = Page.search_fields + [
        # ...
        index.SearchField('get_related_link_titles'),
    ]
```

(modelsearch_indexing_models)=

## Indexing custom models

Any Django model can be indexed and searched.

To do this, inherit from `index.Indexed` and add some `search_fields` to the model.

```python
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

# As this model doesn't have a search method in its QuerySet, we have to call search directly on the backend
>>> from modelsearch.backends import get_search_backend
>>> s = get_search_backend()

# Run a search for a book by Roald Dahl
>>> roald_dahl = Author.objects.get(name="Roald Dahl")
>>> s.search("chocolate factory", Book.objects.filter(author=roald_dahl))
[<Book: Charlie and the chocolate factory>]
```
