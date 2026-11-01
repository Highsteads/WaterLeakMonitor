#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    test_xml_callbacks_exist.py
# Description: Every method MenuItems.xml / PluginConfig.xml names must exist on
#              the Plugin class. Indigo resolves them by name only when the user
#              clicks, so a typo or a rename is otherwise invisible until then.
# Author:      CliveS & Claude
# Date:        01-11-2026
# Version:     1.0

import os
import xml.etree.ElementTree as ET

import pytest

from _harness import SERVER_DIR, wlm

XML_FILES       = ("MenuItems.xml", "PluginConfig.xml", "Actions.xml",
                   "Devices.xml", "Events.xml")
METHOD_ELEMENTS = ("CallbackMethod", "ButtonMethod", "ValidationMethod")


def _referenced():
    found = []
    for name in XML_FILES:
        path = os.path.join(SERVER_DIR, name)
        if not os.path.exists(path):
            continue
        for el in ET.parse(path).getroot().iter():
            if el.tag in METHOD_ELEMENTS and (el.text or "").strip():
                found.append((name, el.text.strip()))
            if el.tag == "List" and el.get("class") == "self" and el.get("method"):
                found.append((name, el.get("method")))
    return found


REFERENCED = _referenced()


def test_the_xml_names_some_methods():
    assert len(REFERENCED) >= 3, REFERENCED


@pytest.mark.parametrize("xml_file,method", REFERENCED,
                         ids=[f"{f}:{m}" for f, m in REFERENCED])
def test_every_xml_callback_exists_on_the_plugin(xml_file, method):
    attr = getattr(wlm.Plugin, method, None)
    assert callable(attr), (
        f"{xml_file} names '{method}', but the Plugin class has no such method")
