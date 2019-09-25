#!/usr/bin/env bash
# Copyright (c) 2009 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

base_dir=$(dirname "$0")

if [[ "#grep#fetch#cleanup#diff#setdep#" != *"#$1#"* ]]; then
  "$base_dir"/update_depot_tools "$@"
  case $? in
    123)
      # msys environment was upgraded, need to quit.
      exit 0
      ;;
    0)
      ;;
    *)
      exit $?
  esac
fi

# Ensure that "depot_tools" is somewhere in PATH so this tool can be used
# standalone, but allow other PATH manipulations to take priority.
PATH=$PATH:$base_dir

if [[ "X$GCLIENT_PY3" != "X1" ]]; then
  PYTHONDONTWRITEBYTECODE=1 exec python "$base_dir/gclient.py" "$@"
else
  PYTHONDONTWRITEBYTECODE=1 exec vpython3 "$base_dir/gclient.py" "$@"
fi
