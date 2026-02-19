"""
Compute caching

django.util.cache works to manage web browser caching.

This code is for caching the server-side computation of database queries.
Cache invalidatation is (a) done explicitly, or (b) a maximum age of
a cached item can be given.  The cache is kept on-disk.  All files are
keep in one directory subtree.  The filenames can have multiple parts
that are used to create subdirectories for faster lookup.

Since the cache is disk-based, using the file timestamps (with nanosecond
granularity) was chosen over using the database's table update times.
If the update times were reliable (eg., MySQL InnoDB tables had issues),
it would avoid the need for a timestamp file.  But it would also add
latency since a database query is slower than stat'ing a file.

"""
import os
import tempfile
import time
import contextlib
import json

A_DAY = 24 * 60 * 60  # 1 day in seconds


class ComputeCache:
    """
    Cached data is kept in a file identified by path components.

    A timestamp file is used to tell when items in the cache are
    out of date.

    If a max_age is set, then cached items are invalid if they are
    more than the max_age (in seconds) old.
    """

    def __init__(self, timestamp, cache_root="/var/tmp", binary=False, max_age=None):
        self.cache_root = cache_root
        self.timestamp = os.path.join(self.cache_root, timestamp)
        self.binary = binary
        if max_age:
            assert max_age > 0, ValueError("max_age must be positive")
            self.max_age_ns = int(max_age * 1_000_000_000)   # convert to nanoseconds
        else:
            self.max_age_ns = max_age
        if not os.path.exists(self.timestamp):
            os.makedirs(self.cache_root, exist_ok=True)
            self.invalidate_timestamp()

    def getfile(self, *path, use_binary=False):
        """Get data from cache

        Return None if too old or missing.
        Otherwise, return binary file object with data.
        """
        if len(path) == 0:
           raise ValueError("path has to have at least one component")
        filename = os.path.join(self.cache_root, *path)
        try:
            ts = os.stat(self.timestamp)
        except OSError:
            # should never happen since timestamp file
            # is created during __init__
            return contextlib.nullcontext(None)

        try:
            if use_binary or self.binary:
                open_args = {'mode': 'rb'}
            else:
                open_args = {'mode': 'r', 'encoding': 'utf-8'}
            info = open(filename, **open_args)
        except OSError:
            # nothing cached yet
            return contextlib.nullcontext(None)
        info_ts = os.fstat(info.fileno())
        if ts.st_mtime_ns > info_ts.st_mtime_ns:
            # cached item is older than timestamp
            return contextlib.nullcontext(None)
        if self.max_age_ns:
            if info_ts.st_mtime_ns < time.time_ns() - self.max_age_ns:
                # cached item is more than max_age old
                return contextlib.nullcontext(None)
        return info

    @contextlib.contextmanager
    def savefile(self, *path):
        """Return file object to save data too

        Should be used with 'with' statement"""
        if len(path) == 0:
           raise ValueError("path has to have at least one component")
        # use temporary filename, and
        # rename to avoid corruption
        dirname = os.path.join(self.cache_root, *path[:-1])
        filename = os.path.join(dirname, path[-1])
        os.makedirs(dirname, exist_ok=True)
        fileno, tempname = tempfile.mkstemp(dir=self.cache_root)
        if self.binary:
            open_args = {'mode': 'wb'}
        else:
            open_args = {'mode': 'w', 'encoding': 'utf-8'}
        with os.fdopen(fileno, **open_args) as f:
            yield f
        os.rename(tempname, filename)

    def invalidate_timestamp(self):
        """Invalidate items in cache"""
        # sleep a nanosecond to ensure timestamp is newer than
        # any cached file
        time.sleep(1e-9)  # a nanosecond
        t = time.time_ns()
        try:
            os.utime(self.timestamp, ns=(t, t))
        except FileNotFoundError:
            with os.open(self.timestamp, os.O_CREAT, mode=0o644) as fileno:
                os.close(fileno)


class JSONComputeCache(ComputeCache):
    """Specialized cache for using JSON on disk"""

    def __init__(self, timestamp, cache_root="/var/tmp", max_age=None):
        # underlying file is always utf-8 encoded
        super().__init__(timestamp, cache_root=cache_root, binary=False, max_age=max_age)

    def get(self, *path):
        """Return Python object from JSON data"""
        with self.getfile(*path) as f:
            if f is None:
                return None
            return json.load(f)

    def get_raw(self, *path):
        """Get cache in binary form"""
        with self.getfile(*path, use_binary=True) as f:
            if f is None:
                return None
            return f.read()

    def save(self, data, *path):
        """Save Python data object as JSON"""
        with self.savefile(*path) as f:
            # minimize file size
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))


def test():
    """test code"""
    # in JSON, all dictionary keys come back as strings
    cache_root = "/tmp/test_test"
    data = [1, {"2": 3}]
    cache = JSONComputeCache("test_ts", cache_root=cache_root, max_age=A_DAY)
    location = "test_data"
    tmp = cache.get(location)
    if tmp is not None:
        print("cache not empty")
    cache.save(data, location)
    data2 = cache.get(location)
    if data == data2:
        print("same")
    else:
        print('in:', data)
        print('out:', data2)

    # test invalidate_timestamp
    # - data already saved above
    cache.invalidate_timestamp()
    tmp = cache.get(location)
    print(f"cache {'NOT ' if tmp is not None else ''}invalidated")

    # test data max_age
    cache.save(data, location)
    t = time.time() - 2 * A_DAY
    os.utime(f"{cache_root}/{location}", times=(t, t))
    tmp = cache.get(location)
    print(f"cache {'NOT ' if tmp is not None else ''}invalidated")


if __name__ == "__main__":
    test()
