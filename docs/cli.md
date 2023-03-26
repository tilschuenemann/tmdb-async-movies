# CLI

## Examples

Looking up a movie from standard input:

```shell
tmdbasyncmovies from_input "1999 The Matrix"
```

---

Looking up multiple movies from standard input:

```shell
tmdbasyncmovies from_input "1999 The Matrix" "2003 The Matrix Revolutions"
```

---

Looking up movies from a parent directory looks like this - note that both items are folders, not video files!

```shell
ls /my/movie/dir
.
..
1999 The Matrix
2003 The Matrix Reloaded
```

```shell
tmdbasyncmovies from_dir /my/movie/dir
```

## Commands and Options

```{eval-rst}
.. click:: tmdb_async_movies.cli:tmdbasyncmovies
    :prog: tmdbasyncmovies
    :nested: full
```
