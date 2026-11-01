#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_changelog_current.py
# Description: docs/changelog.md (the published version history) must lead with
#              the version Info.plist ships, and list no version twice.
#              test_version_consistency.py covers plugin.py and the README; the
#              docs site is a separate page and the one a user reads.
# Author:      CliveS & Claude
# Date:        01-11-2026
# Version:     1.0

import plistlib
import re
from pathlib import Path

REPO      = Path(__file__).resolve().parent.parent
PLIST     = REPO / "WaterLeakMonitor.indigoPlugin" / "Contents" / "Info.plist"
CHANGELOG = REPO / "docs" / "changelog.md"
HEADING   = re.compile(r"^##\s+v?(\d+(?:\.\d+)+)\b", re.MULTILINE)


def _plist_version():
    with open(PLIST, "rb") as f:
        return str(plistlib.load(f)["PluginVersion"])


def test_changelog_newest_entry_is_the_shipped_version():
    versions = HEADING.findall(CHANGELOG.read_text(encoding="utf-8"))
    assert versions, "docs/changelog.md has no '## <version>' headings"
    assert versions[0] == _plist_version(), (
        f"docs/changelog.md leads with {versions[0]}, Info.plist ships {_plist_version()}")


def test_changelog_has_no_duplicate_version_headings():
    versions = HEADING.findall(CHANGELOG.read_text(encoding="utf-8"))
    dupes = sorted({v for v in versions if versions.count(v) > 1})
    assert not dupes, f"listed twice in docs/changelog.md: {dupes}"
