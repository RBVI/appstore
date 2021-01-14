# vim: set expandtab shiftwidth=4:

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
import re
from wheel_filename import parse_wheel_filename, InvalidFilenameError
from packaging.version import Version


class Bundle:
    def __init__(self, filename):
        import pkginfo
        # do a few sanity checks
        w = parse_wheel_filename(filename)   # throws ValueError if illegal
        Version(w.version)  # throw ValueError if version isn't legal
        if len(w.platform_tags) != 1:
            raise ValueError("Bundles are limited to one platform")

        self.path = filename    # Used by apps/devel to mass release bundles
        self._wheel = pkginfo.Wheel(filename)
        self._dist_info = self.package + '-' + self.version + '.dist-info'
        self._zip = None
        platform = w.platform_tags[0]
        if platform.startswith("macosx_"):
            self.platform = "macOS"
        elif platform.startswith("win_"):
            self.platform = "Windows"
        elif platform.startswith(("linux_", "manylinux")):
            self.platform = "Linux"
        elif platform == "any":
            self.platform = ""
        else:
            self.platform = "Unknown"
        if self.platform:
            self.display_name = "%s (%s, %s)" % (self.package, self.version,
                                                 self.platform)
        else:
            self.display_name = "%s (%s)" % (self.package, self.version)

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
        for classifier in self._wheel.classifiers:
            parts = [s.strip() for s in classifier.split("::")]
            if parts[0] != "ChimeraX":
                continue
            info_type = parts[1].lower()
            if info_type == "bundle":
                # ChimeraX :: Bundle :: categories :: session_versions :: api_module_name :: supercedes :: custom_init
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
                # ChimeraX :: Tool :: tool_name :: categories :: synopsis
                # ChimeraX :: Command :: name :: categories :: synopsis
                if len(parts) != 5:
                    continue
                name = parts[2]
                value = {
                    "categories": get_list_items(parts[3]),
                    "synopsis": parts[4],
                }
            elif info_type == "selector":
                # Selector :: name :: synopsis [:: atomic]
                if len(parts) not in (4, 5):
                    continue
                name = parts[2]
                value = {
                    "synopsis": parts[3]
                }
                if len(parts) == 5:
                    value["atomic"] = parts[4]
            elif info_type == "dataformat":
                # Obsolete, pre-1.0
                # ChimeraX :: DataFormat :: format_name :: nicknames :: category :: suffixes :: mime_types :: url :: dangerous :: icon :: synopsis :: encoding
                if len(parts) not in (11, 12):
                    continue
                name = parts[2]
                value = {
                    "nicknames": get_list_items(parts[3]),
                    "category": parts[4],
                    "suffixes": get_list_items(parts[5]),
                    "mime_types": get_list_items(parts[6]),
                    "url": parts[7],
                    "dangerous": parts[8],
                    "icon": parts[9],
                    "synopsis": parts[10],
                }
                if len(parts) == 12:
                    value["encoding"] = parts[11]
            elif info_type == "fetch":
                # Obsolete, pre-1.0
                # ChimeraX :: Fetch :: database_name :: format_name :: prefixes :: example_id :: is_default
                if len(parts) != 7:
                    continue
                name = parts[2]
                value = {
                    "format": parts[3],
                    "suffixes": get_list_items(parts[4]),
                    "example": parts[5],
                    "is_default": parts[6],
                }
            elif info_type in ["open", "save"]:
                # Obsolete, pre-1.0
                # ChimeraX :: Open :: format_name :: tag :: is_default :: keyword_arguments
                # ChimeraX :: Save :: format_name :: tag :: is_default :: keyword_arguments
                if len(parts) not in [5, 6]:
                    continue
                name = parts[2]
                value = {
                    "tag": parts[3],
                    "is_default": parts[4],
                }
                if len(parts) == 6:
                    value["keywords"] = get_list_items(parts[5])
            elif info_type == 'manager':
                # ChimeraX :: Mangager :: name [:: key:value]*
                if len(parts) < 3:
                    continue
                name = parts[2]
                value = {}
                for p in parts[3:]:
                    k, v = p.split(':', 1)
                    if v[0] in '\'"':
                        v = unescape(v[1:-1])
                    else:
                        v = unescape(v)
                    value[k] = v
            elif info_type == 'provider':
                # ChimeraX :: Provider :: name :: manager [:: key:value]*
                if len(parts) < 4:
                    continue
                name = f"{parts[3]}/{parts[2]}"  # manager / name
                value = {}
                for p in parts[4:]:
                    k, v = p.split(':', 1)
                    if v[0] in '\'"':
                        v = unescape(v[1:-1])
                    else:
                        v = unescape(v)
                    value[k] = v
            else:
                # See chimerax/src/core/toolshed/installed.py for possibilities
                # ChimeraX :: DataDir :: directory
                # ChimeraX :: IncludeDir :: directory
                # ChimeraX :: LibraryDir :: directory
                # ChimeraX :: ExecutableDir :: directory
                # or unknown ChimeraX metadata type, ignore for now
                continue
            for k, v in list(value.items()):
                if not v:
                    del value[k]
            d = container.setdefault(info_type, {})
            d[name] = value
        return container

    def __unicode__(self):
        return self._wheel.name

    @property
    def package(self):
        return self._wheel.name.replace('-', '_')

    @property
    def version(self):
        return self._wheel.version

    @property
    def summary(self):
        return self._wheel.summary

    @property
    def requires(self):
        return self._wheel.requires_dist

    @property
    def zip(self):
        if not self._zip:
            import zipfile
            self._zip = zipfile.ZipFile(self.path)
        return self._zip

    @property
    def screenshot(self):
        try:
            return self._screenshot
        except AttributeError:
            try:
                ss = self.zip.read("%s/screenshot.png" % self._dist_info)
            except KeyError:
                ss = None
            self._screenshot = ss
            return ss

    @property
    def release_notes(self):
        try:
            return self._release_notes
        except AttributeError:
            try:
                ss = self.zip.read("%s/RELNOTES.html" % self._dist_info)
            except KeyError:
                ss = None
            self._release_notes = ss
            return ss


def compatible_with(version, needed_version):
    if needed_version.startswith('('):
        assert needed_version[-1] == ')'
        needed_version = needed_version[1:-1]
    from packaging.specifiers import SpecifierSet
    spec = SpecifierSet(needed_version, prereleases=True)
    return spec.contains(version)


REUAChimeraX = re.compile(r".*UCSF-ChimeraX/(?P<version>\S+) "
                          r"\((?P<platform>.*)\).*")


def chimerax_user_agent(request):
    """Return ChimeraX version and platform from user agent string."""

    m = REUAChimeraX.match(request.META.get("HTTP_USER_AGENT", ""))
    if m:
        # Note that we only use the ChimeraX-provided information
        # instead of the more general user agent data.  The platform
        # from ChimeraX derives from "platform.system()" in Python 3.
        version = m.group("version")
        platform = m.group("platform")
        platform, *platform_version = platform.split()
        # platform_version = ' '.join(platform_version)
        if platform == "Darwin":
            platform = "macOS"
        return version, platform
    else:
        return None, None


_escape_table = {
    "'": "'",
    '"': '"',
    '\\': '\\',
    '\n': '',
    'a': '\a',  # alarm
    'b': '\b',  # backspace
    'f': '\f',  # formfeed
    'n': '\n',  # newline
    'r': '\r',  # return
    't': '\t',  # tab
    'v': '\v',  # vertical tab
}


def unescape(text):
    """Replace backslash escape sequences with actual character.

    :param text: the input text
    :returns: the processed text

    Follows Python's :ref:`string literal <python:literals>` syntax
    for escape sequences."""
    return unescape_with_index_map(text)[0]


def unescape_with_index_map(text):
    """Replace backslash escape sequences with actual character.

    :param text: the input text
    :returns: the processed text and index map from processed to input text

    Follows Python's :ref:`string literal <python:literals>` syntax
    for escape sequences."""
    # standard Python backslashes including \N{unicode name}
    start = 0
    index_map = list(range(len(text)))
    while start < len(text):
        index = text.find('\\', start)
        if index == -1:
            break
        if index == len(text) - 1:
            break
        escaped = text[index + 1]
        if escaped in _escape_table:
            text = text[:index] + _escape_table[escaped] + text[index + 2:]
            # Assumes that replacement is a single character
            index_map = index_map[:index] + index_map[index + 1:]
            start = index + 1
        elif escaped in '01234567':
            # up to 3 octal digits
            for count in range(2, 5):
                if text[index + count] not in '01234567':
                    break
            try:
                char = chr(int(text[index + 1: index + count], 8))
                text = text[:index] + char + text[index + count:]
                index_map = index_map[:index] + index_map[index + count - 1:]
            except ValueError:
                pass
            start = index + 1
        elif escaped == 'x':
            # 2 hex digits
            try:
                char = chr(int(text[index + 2: index + 4], 16))
                text = text[:index] + char + text[index + 4:]
                index_map = index_map[:index] + index_map[index + 3:]
            except ValueError:
                pass
            start = index + 1
        elif escaped == 'u':
            # 4 hex digits
            try:
                char = chr(int(text[index + 2: index + 6], 16))
                text = text[:index] + char + text[index + 6:]
                index_map = index_map[:index] + index_map[index + 5:]
            except ValueError:
                pass
            start = index + 1
        elif escaped == 'U':
            # 8 hex digits
            try:
                char = chr(int(text[index + 2: index + 10], 16))
                text = text[:index] + char + text[index + 10:]
                index_map = index_map[:index] + index_map[index + 9:]
            except ValueError:
                pass
            start = index + 1
        elif escaped == 'N':
            # named unicode character
            if len(text) < index + 2 or text[index + 2] != '{':
                start = index + 1
                continue
            end = text.find('}', index + 3)
            if end > 0:
                import unicodedata
                char_name = text[index + 3:end]
                try:
                    char = unicodedata.lookup(char_name)
                    text = text[:index] + char + text[end + 1:]
                    index_map = index_map[:index] + index_map[end:]
                except KeyError:
                    pass
            start = index + 1
        else:
            # leave backslash in text like Python
            start = index + 1
    return text, index_map


if __name__ == "__main__":
    if True:
        v = Version("0.9.2")
        need = [
            "(>=0.1)",
            "(==0.8)",
            "(>=0.8)",
            "(==0.9.2)",
            "(>0.9.1,<1)",
            "(~=0.9.1)",
            "(~=0.9.3)"
        ]
        print(v)
        for n in need:
            print(n, compatible_with(v, n))
    if True:
        v1 = Version("1.0.1")
        v1b1 = Version("1.0.1b1")
        v1b2 = Version("1.0.1b2")
        v2 = Version("1.0.2")
        print(v1 > v1b1, "should be True")
        print(v1b2 < v1b1, "should be False")
        print(v1 < v2, "should be True")
        print(v2 < v1b1, "should be False")
    if True:
        import os
        # root = "d:/chimerax/src/bundles"
        root = "testdata"
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if not filename.endswith(".whl"):
                    continue
                b = Bundle(os.path.join(dirpath, filename))
                print("bundle", b.package, b.version, b.platform)
                print("summary", b.summary)
                print("requires", b.requires)
                # print("screenshot", b.screenshot is not None)
                # print("release notes", b.release_notes)
                info = b.info()
                for info_type in sorted(info.keys()):
                    info_data = info[info_type]
                    for name, value in info_data.items():
                        print("info", info_type, name, value)
                print()
