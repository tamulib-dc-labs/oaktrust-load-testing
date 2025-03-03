# OAKTrust Load Tests

This locust implementation is designed to run load tests versus DSPACE instances.

## Installing 

You can install with poetry like:

```shell
$ poetry install
```

## Running

To run, you can:

```shell
$ locust -f src/locustfile.py
```

The default command line arguments have been extended.  The additional arguments are:

**--tasks**

```console
$ locust -f src/locustfile.py --tasks=get_collections,lookup_authors
```

You can specify certain tasks to test, and you can run multiple tasks at a time by comma separating them as the argument
value.  Currently, the tasks are:

* get_collections: Uses the API to randomly choose a collection and request the corresponding URL
* lookup_authors: Uses the search API to randomly select an author and its publications and request them all.
* download_bitstreams: Uses the search API to randomly request and attempt to download a bitstream.

If not specified, the default value is `get_collections` only.

**--url**

```console
$ locust -f src/locustfile.py --url=https://oaktrust-pre.library.tamu.edu
```

You can specify the DSPACE instance to test.

If not specified, the default value is `https://oaktrust-pre.library.tamu.edu` only.

**--log-file**

```console
$ locust -f src/locustfile.py --log-file=default.log
```

You can specify where you want to log messages to.

If not specified, the default value is `default.log`.

**--log-level**

```console
$ locust -f src/locustfile.py --log-level=WARNING
```

You can specify the level to log.  The default is `WARNING`, but you can also use `DEBUG`, `INFO`, `ERROR`, or `CRITICAL`.

