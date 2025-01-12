#-------------------------------------------------------------------------
#
# Batch Apps Blender Addon
#
# Copyright (c) Microsoft Corporation.  All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the ""Software""), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#--------------------------------------------------------------------------
#
# Blender Sample Dependency Install Script
#
# This script is designed to be run with Blender to download the required
# packages to Blenders bundled python environment.
# This script is experimental and is provided as a convenience only.
# The script has currently only been tested under Windows OS.
#
# The script downloads and unpacks the following dependencies:
#   - Azure Batch Apps Python Client v0.3.0
#   - Keyring v4.0
#   - OAuthLib v0.7.2
#   - Requeses-OAuthLib v0.4.2
#
# To run the script, run the following command as an administrator:
#
#   >> blender.exe -b -P dependency_check.py
#
#--------------------------------------------------------------------------

import requests
import os
import bpy
import tarfile
import shutil
import sys
import zipfile
import warnings
import importlib

warnings.simplefilter('ignore')

TEMP_DIR = os.path.join(bpy.context.user_preferences.filepaths.temporary_directory, "batchapps_blender_install")
INSTALL_DIR = os.path.join(sys.prefix, "lib", "site-packages")
LIBS = [
    {"lib":"oauthlib",          "ver":"0.7.2",  "mod":"oauthlib",           "ext":"tar.gz"},
    {"lib":"requests-oauthlib", "ver":"0.4.2",  "mod":"requests_oauthlib",  "ext":"tar.gz"},
    {"lib":"keyring",           "ver":"4.0",    "mod":"keyring",            "ext":"zip"},
    {"lib":"azure-batch-apps",  "ver":"0.3.0",  "mod":"batchapps",          "ext":"tar.gz"}
    ]

def unpack_tar(lib_full, lib_dir, lib_module):

    with tarfile.open(lib_full, 'r:gz') as tfile:
        members = tfile.getmembers()
        mod_path = "{0}/{1}/".format(lib_dir, lib_module)
        subset = [m for m in members if m.path.startswith(mod_path)]
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tfile, path=TEMP_DIR, members=subset)

def unpack_zip(lib_full, lib_dir, lib_module):

    with zipfile.ZipFile(lib_full) as zfile:
        members = zfile.infolist()
        mod_path = "{0}/{1}/".format(lib_dir, lib_module)
        subset = [m for m in members if m.filename.startswith(mod_path)]
        zfile.extractall(path=TEMP_DIR, members=subset)

def download_lib(lib_name, lib_version, lib_module, lib_ext):

    lib_dir = "{0}-{1}".format(lib_name, lib_version)
    lib_file = "{0}.{1}".format(lib_dir, lib_ext)
    lib_full = os.path.join(TEMP_DIR, lib_file)
    lib_url = "http://pypi.python.org/packages/source/{0}/{1}/{2}".format(lib_name[0], lib_name, lib_file)

    lib_inst = os.path.join(INSTALL_DIR, lib_module)

    try:

        print("  - Creating temp dir at: {0}".format(TEMP_DIR))
        if not os.path.exists(TEMP_DIR):    
            os.mkdir(TEMP_DIR)
    
        with open(lib_full, 'wb') as handle:
            print("  - Downloading package from {0}".format(lib_url))
            resp = requests.get(lib_url, stream=True, verify=False)

            if not resp.ok:
                raise Exception(resp.reason)

            for block in resp.iter_content(1024):
                if not block:
                    break

                handle.write(block)

        print("  - Download complete")

        if lib_ext == 'zip':
            unpack_zip(lib_full, lib_dir, lib_module)
        else:
            unpack_tar(lib_full, lib_dir, lib_module)


        print("  - Files unpacked")
        shutil.copytree(os.path.join(TEMP_DIR, lib_dir, lib_module), lib_inst)
        print("  - Files moved to: {0}".format(lib_inst))
        print("  - Successfully installed {0}".format(lib['lib']))
        
    except PermissionError:
        print("  - Failed to install {0}. Please ensure you have administrator"
              " access to the Blender installation directory".format(lib_name))

    except Exception as exp:
        print("  - Failed to install {0}. Error: {1}".format(lib_name, exp))

    finally:
        print("  - Cleaning up temp files")
        shutil.rmtree(TEMP_DIR)

if __name__ == '__main__':

    print("Checking for dependencies...")

    for lib in LIBS:
        try:
            importlib.import_module(lib['mod'])
            print("Found {0}".format(lib['lib']))

        except ImportError:
            print("Missing {0}".format(lib['lib']))
            print("  - Downloading version {0}".format(lib['ver']))
            download_lib(lib['lib'], lib['ver'], lib['mod'], lib['ext'])
    
    print("Dependency check complete!")
    
    
    
