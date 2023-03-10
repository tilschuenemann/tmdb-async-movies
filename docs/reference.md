# Reference

## Naming Conventions

The extraction of year and title from an input string relies on a regex pattern. Multiple patterns are already provided.

If you feel like a pattern is missing, feel free to create a [Pull Request](https://github.com/tilschuenemann/tmdbasync/pulls)!

| Naming Convention # | Input                                                                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0                   | [1999 The Matrix](https://regex-vis.com/?r=%5E%28%3F%3Cyear%3E%5Cd%7B4%7D%29%5Cs%28%3F%3Ctitle%3E.%2B%29%24&e=0&t=%5B%221999+The+Matrix%22%5D)          |
| 1                   | [1999 - The Matrix](https://regex-vis.com/?r=%5E%28%3F%3Cyear%3E%5Cd%7B4%7D%29%5Cs-%5Cs%28%3F%3Ctitle%3E.%2B%29%24&e=0&t=%5B%221999+-+The+Matrix%22%5D) |

```{eval-rst}
.. tip::
  You can click the link in the second column to get a visual representation. You can also test if your examples match!
```

## Schemas

All dataframes types are cast as follows:

```{eval-rst}
.. literalinclude:: ../src/tmdbasync/main.py
   :language: python
   :pyobject: Tmdb._get_schema
```
