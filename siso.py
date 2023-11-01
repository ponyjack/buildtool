#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""This script is a wrapper around the siso binary that is pulled to
third_party as part of gclient sync. It will automatically find the siso
binary when run inside a gclient source tree, so users can just type
"siso" on the command line."""

import os
import signal
import subprocess
import sys

import gclient_paths


def main(args):
    signal.signal(signal.SIGINT, lambda signum, frame: None)

    # On Windows the siso.bat script passes along the arguments enclosed in
    # double quotes. This prevents multiple levels of parsing of the special '^'
    # characters needed when compiling a single file.  When this case is
    # detected, we need to split the argument. This means that arguments
    # containing actual spaces are not supported by siso.bat, but that is not a
    # real limitation.
    if sys.platform.startswith('win') and len(args) == 2:
        args = args[:1] + args[1].split()

    # macOS's python sets CPATH, LIBRARY_PATH, SDKROOT implicitly.
    # https://openradar.appspot.com/radar?id=5608755232243712
    #
    # Removing those environment variables to avoid affecting clang's behaviors.
    if sys.platform == 'darwin':
        os.environ.pop("CPATH", None)
        os.environ.pop("LIBRARY_PATH", None)
        os.environ.pop("SDKROOT", None)

    environ = os.environ.copy()

    # Get gclient root + src.
    primary_solution_path = gclient_paths.GetPrimarySolutionPath()
    gclient_root_path = gclient_paths.FindGclientRoot(os.getcwd())
    gclient_src_root_path = None
    if gclient_root_path:
        gclient_src_root_path = os.path.join(gclient_root_path, 'src')

    siso_override_path = os.environ.get('SISO_PATH')
    if siso_override_path:
        print('depot_tools/siso.py: Using Siso binary from SISO_PATH: %s.' %
              siso_override_path)
        if not os.path.isfile(siso_override_path):
            print(
                'depot_tools/siso.py: Could not find Siso at provided '
                'SISO_PATH.',
                file=sys.stderr)
            return 1

    for base_path in set(
        [primary_solution_path, gclient_root_path, gclient_src_root_path]):
        if not base_path:
            continue
        env = environ.copy()
        sisoenv_path = os.path.join(base_path, 'build', 'config', 'siso',
                                    '.sisoenv')
        if not os.path.exists(sisoenv_path):
            continue
        with open(sisoenv_path) as f:
            for line in f.readlines():
                k, v = line.rstrip().split('=', 1)
                env[k] = v
        siso_path = siso_override_path or os.path.join(
            base_path, 'third_party', 'siso',
            'siso' + gclient_paths.GetExeSuffix())
        if os.path.isfile(siso_path):
            return subprocess.call([siso_path] + args[1:], env=env)

    print(
        'depot_tools/siso.py: Could not find .sisoenv under build/config/siso '
        'of the current project. Did you run gclient sync?',
        file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
