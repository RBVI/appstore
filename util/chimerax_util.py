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

if __name__ == "__main__":
    import types
    b = Bundle("chimerax.model_panel-1.0-py3-none-any.whl")
    print "bundle", b, b.package, b.version
    print "summary", b.summary
    print "screenshot", b.screenshot
    print "screenshot", b.screenshot
    print "metadata", b.metadata
