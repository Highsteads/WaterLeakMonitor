#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Filename:    _harness.py
# Description: Gives the tests/ folder the SAME indigo stand-in and fixtures as
#              the bundle's own test_plugin.py, by importing it. Two different
#              stand-ins in one pytest run would fight over sys.modules["indigo"]
#              and over the cached `plugin` module, so there is exactly one.
# Author:      CliveS & Claude
# Date:        01-11-2026
# Version:     1.0

import os
import sys

SERVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                          "WaterLeakMonitor.indigoPlugin", "Contents", "Server Plugin")
SERVER_DIR = os.path.normpath(SERVER_DIR)
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

import test_plugin as tp   # noqa: E402  — installs the stub and imports plugin

wlm          = tp.wlm
indigo_stub  = tp._ind
FakeSensor   = tp.FakeSensor
make_plugin  = tp.make_plugin
reset_server = tp._reset_server
SENSOR_ID    = tp.SENSOR_ID
