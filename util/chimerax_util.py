# vim: set expandtab shiftwidth=4 softtabstop=4:

"""
chimerax_util: ChimeraX-specific utilities
=========================================================

This module contains code for handling ChimeraX bundles.

A :py:class:`Bundle` instance is initialized from a
ChimeraX bundle, which is a Python "wheel" with additional
standardized contents such as icon and screenshots.
Callers may query :py:class:`Bundle` instances for information
such as bundle name, version, dependencies, description, summary,
icon, screenshot, etc.
"""

class Bundle:
    def __init__(self, filename):
        from zipfile import ZipFile
        import json
        # Wheels are zip files
        self.zip = z = ZipFile(filename)

        # Look for toplevel directory that ends with ".dist-info"
        # This directory contains the wheel metadata
        distinfo = None
        for name in z.namelist():
            components = name.split('/')
            if components[0].endswith(".dist-info"):
                if distinfo is not None and distinfo != components[0]:
                    raise ValueError("too many .dist-info directories")
                distinfo = components[0]
        self.distinfo = distinfo

        # Parse distinfo into package and version
        parts = distinfo.rsplit('.', 1)[0].rsplit('-', 1)
        if len(parts) != 2:
            raise ValueError("unsupported .dist-info name")
        self.package, self.version = parts
        self._pkg_path = self.package.replace('.', '/')

        # Read metadata using the json-format file
        self.metadata = json.loads(z.read("%s/metadata.json" % distinfo))
        if self.metadata["version"] != self.version:
            raise ValueError("internal version mismatch")

    def info(self):
        # This code parses the bundle metadata in the same way
        # found in chimerax/src/core/toolshed/__init__.py
        def get_list_items(s):
            # Assume s is already stripped
            if not s:
                return None
            else:
                return [i.strip() for i in s.split(',')]
        container = {}
        for classifier in self.metadata.get("classifiers", []):
            parts = [s.strip() for s in classifier.split("::")]
            if parts[0] != "ChimeraX":
                continue
            info_type = parts[1].lower()
            if info_type == "bundle":
                if len(parts) != 7:
                    continue
                name = self.package
                value = {
                    "categories": get_list_items(parts[2]),
                    "session_versions": parts[3],
                    "app_package_name": parts[4],
                    "supercedes": parts[5],
                    "custom_init": parts[6],
                }
            elif info_type in ["command", "tool"]:
                if len(parts) != 5:
                    continue
                name = parts[2]
                value = {
                    "categories":get_list_items(parts[3]),
                    "synopsis":parts[4],
                }
            elif info_type == "selector":
                if len(parts) != 4 and len(parts) != 5:
                    continue
                name = parts[2]
                value = {
                    "synopsis":parts[3]
                }
                if len(parts) == 5:
                    value["atomic"] = parts[4]
            elif info_type == "dataformat":
                if len(parts) not in [11,12]:
                    continue
                name = parts[2]
                value = {
                    "nicknames":get_list_items(parts[3]),
                    "category":parts[4],
                    "suffixes":get_list_items(parts[5]),
                    "mime_types":get_list_items(parts[6]),
                    "url":parts[7],
                    "dangerous":parts[8],
                    "icon":parts[9],
                    "synopsis":parts[10],
                }
                if len(parts) == 12:
                    value["encoding"] = parts[11]
            elif info_type == "fetch":
                if len(parts) != 7:
                    continue
                name = parts[2]
                value = {
                    "format":parts[3],
                    "suffixes":get_list_items(parts[4]),
                    "example":parts[5],
                    "is_default":parts[6],
                }
            elif info_type in ["open", "save"]:
                if len(parts) not in [5,6]:
                    continue
                name = parts[2]
                value = {
                    "tag":parts[3],
                    "is_default":parts[4],
                }
                if len(parts) == 6:
                    value["keywords"] = get_list_items(parts[5])
            else:
                # unknown ChimeraX metadata type, ignore for now
                continue
            for k, v in list(value.items()):
                if not v:
                    del value[k]
            d = container.setdefault(info_type, {})
            d[name] = value
        return container

    @property
    def summary(self):
        return self.metadata.get("summary")

    @property
    def requires(self):
        return self.metadata.get("run_requires")

    @property
    def screenshot(self):
        try:
            return self._screenshot
        except AttributeError:
            try:
                ss = self.zip.read("%s/screenshot.png" % self._pkg_path)
            except KeyError:
                ss = None
            self._screenshot = ss
            return ss


class Version:
    """Version is similar to distutils.version.StrictVersion
    but allows for more than three digits before an optional
    alphanumeric label.  Unlike StrictVersion, the trailing
    alphanumeric label part is compared as a string rather
    than further broken into an alphabetic label and an
    integer version number.  This is to avoid having to
    handle illegal version numbers, but it does mean the
    sorting might go a1<a10<a2."""

    def __init__(self, s):
        self._raw = s
        n = 0
        while n < len(s):
            if s[n].isdigit() or s[n] != '.':
                n += 1
            else:
                break
        self.value = [int(v) for v in s[:n].split('.')]
        if n < len(s):
            self.value.append(s[n:])

    def __cmp__(self, other):
        n = 0
        limit = min(len(self.value), len(other.value))
        for n in range(limit):
            if isinstance(self.value[n], int):
                if isinstance(other.value[n], int):
                    # Both integers
                    delta = self.value[n] - other.value[n]
                    if delta == 0:
                        # Same version so far
                        continue
                    else:
                        # Different version at n
                        return delta
                else:
                    # Version with more integers is "larger"
                    return 1
            else:
                if isinstance(other.value[n], int):
                    # Version with more integers is "larger"
                    return -1
                else:
                    # Both non-integers
                    delta = cmp(self.value[n], other.value[n])
                    if delta == 0:
                        # Same version so far
                        continue
                    else:
                        return delta
        # Same all the way through, longer is "larger"
        return cmp(len(self.value), len(other.value))


if __name__ == "__main__":
    v1 = Version("1.0.1")
    v1b1 = Version("1.0.1b1")
    v1b2 = Version("1.0.1b2")
    v2 = Version("1.0.2")
    print v1 < v1b1, "should be True"
    print v1b2 < v1b1, "should be False"
    print v1 < v2, "should be True"
    print v2 < v1b1, "should be False"
    raise SystemExit(0)
    import os, os.path
    # root = "d:/chimerax/src/bundles"
    root = "testdata"
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith(".whl"):
                continue
            b = Bundle(os.path.join(dirpath, filename))
            print "bundle", b.package, b.version, b.platform
            print "summary", b.summary
            print "screenshot", b.screenshot
            # print "metadata", b.metadata
            info = b.info()
            for info_type in sorted(info.keys()):
                info_data = info[info_type]
                for name, value in info_data.items():
                    print info_type, name, value
            print
