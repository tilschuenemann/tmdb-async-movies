# CLI

```{eval-rst}
.. click:: tmdbasyncmovies.cli:tmdbasyncmovies
    :prog: tmdbasyncmovies
    :nested: full
```

## CLI Examples

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

Looking up movies from a movie directory makes the assumption that it's structured like this:

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
