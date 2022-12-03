# Features

## Metadata Format & Structure

All dataframes types are cast as follows:

```{eval-rst}
.. literalinclude:: ../src/movieparse/main.py
   :language: python
   :pyobject: Movieparse._assign_types
```

tmdb_id is listed in mapping.csv only, but also present in all other dataframes.

## Manual ID Mapping

Due to grabbing the most popular match for a given title and release year from the TMDB API, results might not always be the movie you're looking for.

If you notice that tmdb_id doesn't match your expected movie, you can specify a `tmdb_id_man` yourself in `mapping.csv`:

| tmdb_id | tmdb_id_man | input           | canonical_input |
| ------- | ----------- | --------------- | --------------- |
| 123     | **603**     | 1999 The Matrix | 1999 The Matrix |

The next time you run movieparse, metadata will be looked up for both ids `123` and `603`.

## Parsing Styles

### Supported Patterns & Examples

For extracting release year and title multiple patterns are provided. These will be showcased with this data:

| year | title      |
| ---- | ---------- |
| 1999 | The Matrix |

| Pattern # | Input                                                                                                                                                   |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0         | [1999 The Matrix](https://regex-vis.com/?r=%5E%28%3F%3Cyear%3E%5Cd%7B4%7D%29%5Cs%28%3F%3Ctitle%3E.%2B%29%24&e=0&t=%5B%221999+The+Matrix%22%5D)          |
| 1         | [1999 - The Matrix](https://regex-vis.com/?r=%5E%28%3F%3Cyear%3E%5Cd%7B4%7D%29%5Cs-%5Cs%28%3F%3Ctitle%3E.%2B%29%24&e=0&t=%5B%221999+-+The+Matrix%22%5D) |
| 2         | [The Matrix - 1999](https://regex-vis.com/?r=%5E%28%3F%3Ctitle%3E.%2B%29%5Cs-%5Cs%28%3F%3Cyear%3E%5Cd%7B4%7D%29%24&e=0&t=%5B%22The+Matrix+-+1999%22%5D) |

```{eval-rst}
.. tip::
  You can click the link in the second column to get a visual representation on regex-vis. You can also test if your examples match!
```

```{eval-rst}
.. literalinclude:: ../src/movieparse/main.py
   :language: python
   :pyobject: Movieparse.get_parsing_patterns
   :caption: To get a list of valid styles, you can run Movieparse.get_parsing_patterns():
```

### Unsupported Patterns

If you feel like a pattern is missing, feel free to create a [Pull Request](https://github.com/tilschuenemann/movieparse/pulls)!

### Automatic Choice of Patterns

Leaving the `parsing_style` argument empty defaults to `-1`, therefore the best for your input is estimated.

Your input gets extracted by all patterns and the pattern with the highest accuracy gets used for the lookups.
For input that doesn't comply with the chosen pattern, no lookups will be made.

If you're using `strict: True`, a fallback lookup may be made with title only.

## Error Codes / Invalid Ids

```{eval-rst}
.. literalinclude:: ../src/movieparse/main.py
   :language: python
   :lines: 41-45
   :caption: Movieparse.default_codes
```
