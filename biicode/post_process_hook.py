"""
    wxWidgets hook file. You can change the default options to configure wxWidgets. Change this
    local variable (depending on your OS):
        
        $ export BII_WX_CONFIG_OPTIONS="--enable-unicode"

    Note: If you are on Windows OS, you can change an environment var, BII_WX_COMPILE_TOOL
          to indicate the tool to compile your project and build the wxWidgets
          (by default, BII_WX_COMPILE_TOOL='MinGW')

        $ set BII_WX_COMPILE_TOOL=Visual Studio 10
"""

import shutil
import os
import platform
import sys

######################## GLOBAL VARIABLES ########################

install_folder = os.path.join(bii.environment_folder, "wxWidgets/3.0.2/")  # .biicode/wxWidgets/3.0.2/
decomp_folder = os.path.join(bii.environment_folder, 'wxWidgets-3.0.2')
build_folder = os.path.join(install_folder, "build")  # .biicode/wxWidgets/3.0.2/build
sources_folder = os.path.join(install_folder, "sources")  # .biicode/wxWidgets/3.0.2/build

_platform = platform.system()
win_platform = _platform == "Windows"
darwin_platform = _platform == "Darwin"

BII_WX_CONFIGURE_OPTIONS = os.getenv('BII_WX_CONFIG_OPTIONS', None)
win_compiler_tool = os.getenv('BII_WX_COMPILE_TOOL', 'mingw').lower()

if not BII_WX_CONFIGURE_OPTIONS:
    if win_platform:
        # By default, only avalible MinGW y Visual Studio X building
        if win_compiler_tool == 'mingw':
            BII_WX_CONFIGURE_OPTIONS = "-f makefile.gcc SHARED=1 UNICODE=1"
        else:
            try:
                visual_studio_version = win_compiler_tool.split()[2]
            except:
                visual_studio_version = '10'
            BII_WX_CONFIGURE_OPTIONS = "-f makefile.vc SHARED=1"
    elif darwin_platform:
        xcode_sdk_version = os.listdir("/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs")[0]
        command_xcode_sdk = "--with-macosx-sdk=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/%s" % xcode_sdk_version
        BII_WX_CONFIGURE_OPTIONS = '--enable-unicode --with-osx_cocoa --with-macosx-version-min=10.7 %s CC=clang CXX=clang++ CXXFLAGS=-stdlib=libc++ OBJCXXFLAGS=-stdlib=libc++ LDFLAGS=-stdlib=libc++' % command_xcode_sdk
    else:
        BII_WX_CONFIGURE_OPTIONS = '--enable-unicode'

######################## METHODS ########################

def save(path, binary_content):
    with open(path, 'wb') as handle:
        handle.write(binary_content)


def load(path):
    with open(path, 'rb') as handle:
        return handle.read()


def search_and_replace(path, token, replacement):
    try:
        c = load(path)
        c = c.replace(token, replacement)
        save(path, c)
    except:
        pass


def _init_installation():
    if win_platform:
        url = "http://sourceforge.net/projects/wxwindows/files/3.0.2/wxWidgets-3.0.2.zip/download"
        filename = "wxWidgets-3.0.2.zip"
    else:
        url = "http://sourceforge.net/projects/wxwindows/files/3.0.2/wxWidgets-3.0.2.tar.bz2/download"
        filename = "wxWidgets-3.0.2.tar.bz2"

    filepath = os.path.join(bii.environment_folder, filename)  # .biicode/wxWidgets-3.0.2.zip

    # Download wxidgets
    if not os.path.exists(filepath):
        bii.download(url, filepath)
        bii.out.success("\nDownloading finished with success.")

    # Decompressing files wxidgets
    if not os.path.exists(install_folder):
        os.makedirs(install_folder)
    bii.out.info("Decompressing files...")
    if win_platform:
        bii.decompress(filepath, decomp_folder)
    else:
        os.chdir(bii.environment_folder)
        os.system('tar jxf %s' % filepath)


def _copy_build_folder():
    # Lib folder, dynamic libs
    win_lib_folder = 'gcc_dll' if win_compiler_tool == 'mingw' else 'vc_dll'
    wx_dynamic_libs = os.path.join(decomp_folder, 'lib', win_lib_folder) if win_platform else \
                      os.path.join(decomp_folder, 'aux-build', 'lib')

    bii.out.info("Copying the necessary files into .biicode/wxWidgets/3.0.2/build/")
    shutil.copytree(wx_dynamic_libs, build_folder)
    bii.out.success("\nFinished wxWidgets building with success")


def install_wx_widgets_win():
    _init_installation()

    # Install
    win_build_folder = os.path.join(decomp_folder, 'build', 'msw')
    os.chdir(win_build_folder)
    bii.out.info("\nConfiguring and building wxWidgets with %s. It could take several minutes..." % win_compiler_tool)
    if win_compiler_tool == 'mingw':
        setup_h_path = os.path.join(decomp_folder, 'include', 'wx', 'setup.h')
        msw_setup_h_path = os.path.join(decomp_folder, 'include', 'wx', 'msw', 'setup.h')
        if not os.path.exists(setup_h_path):
            shutil.copy(msw_setup_h_path, os.path.join(decomp_folder, 'include', 'wx'))
        os.system(r'mingw32-make -j4 %s' % BII_WX_CONFIGURE_OPTIONS)
    else:  # using Microsoft Visual Studio
        visual_command = r'"C:/Program Files (x86)/Microsoft Visual Studio %s.0/VC/vcvarsall.bat" && nmake.exe %s' % (visual_studio_version,
                                                                                                                      BII_WX_CONFIGURE_OPTIONS)
        os.system(visual_command)
    bii.out.success("\nCompilation finished.")

    _copy_build_folder()


def install_wx_widgets_unix():
    _init_installation()

    # Preventing bug in MacOS 10.10
    if darwin_platform:
        # Bugfix in wxWidgets 3.0.2 if MACOSX_VERSION=10.10
        macosx_10_10_token = r'''#include <WebKit/WebKit.h>'''
        macosx_10_10_fix = r'''#if __MAC_OS_X_VERSION_MAX_ALLOWED >= 101000
                #include <WebKit/WebKitLegacy.h>
        #else
                #include <WebKit/WebKit.h>
        #endif'''
        search_and_replace(os.path.join(decomp_folder, 'src', 'osx', 'webview_webkit.mm'),
                           macosx_10_10_token,
                           macosx_10_10_fix)

    # Build the library, dynamic libs saved in
    os.chdir(decomp_folder)
    aux_build_folder = os.path.join(decomp_folder, 'aux-build')

    # Prepare folder to install
    if not os.path.exists(aux_build_folder):
        os.makedirs(aux_build_folder)
    os.chdir(aux_build_folder)

    def configure_on_linux():
        bii.out.info("Trying to install libgtk-3-dev package...")
        os.system(r'sudo apt-get install libgtk-3-dev')
        bii.out.info("\nConfiguring and building wxWidgets with %s flag. It could take several minutes..." % BII_WX_CONFIGURE_OPTIONS)
        os.system(r'../configure %s' % BII_WX_CONFIGURE_OPTIONS)

    def configure_on_macosx():
        bii.out.info("\nConfiguring and building wxWidgets with %s flags. It could take several minutes..." % BII_WX_CONFIGURE_OPTIONS)
        os.system(r'../configure %s' % BII_WX_CONFIGURE_OPTIONS)

    # Installing
    if darwin_platform:
        configure_on_macosx()
    else:
        configure_on_linux()

    os.system('make -j4')
    bii.out.success("\nCompilation finished.")

    _copy_build_folder()

######################## MAIN CODE ########################

if not os.path.exists(build_folder):
    if win_platform:
        install_wx_widgets_win()
    else:
        install_wx_widgets_unix()
