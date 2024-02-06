#!/usr/bin/env python3

# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import subprocess as sp
import shutil
import os


def find_conan():
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError("Unable to find conan in your PATH.\n"
                           "Please install conan: https://conan.io/downloads")

    return conan


def run_conan_profile_detect(conan):

    sp.run([conan, "profile", "detect"], stderr=sp.DEVNULL, stdout=sp.DEVNULL)


def run_conan_install(conan):
    sp.check_call([conan, "install", os.path.join("..", "conanfile.txt"), "--settings=build_type=Release",
                  "--settings=compiler.cppstd=17", "--output-folder=conan-staging",
                   "--build=missing", "--update"], stdout=sp.DEVNULL)


def main():
    conan = find_conan()
    pwd = os.getcwd()

    conandeps_mk = os.path.join(pwd, "conan-staging", "conandeps.mk")

    if os.path.exists(conandeps_mk):
        print(conandeps_mk)
        return

    conan_home = os.getenv("CONAN_HOME")
    if conan_home is not None:
        os.makedirs(conan_home, exist_ok=True)

        cc = os.getenv("CC")
        if cc is not None:
            new_cc = os.path.join(conan_home, "gcc")
            os.symlink(cc, new_cc)
            os.environ["CC"] = new_cc

        cxx = os.getenv("CXX")
        if cxx is not None:
            new_cxx = os.path.join(conan_home, "g++")
            os.symlink(cc, new_cxx)
            os.environ["CC"] = new_cxx

    run_conan_profile_detect(conan)
    run_conan_install(conan)
    print(conandeps_mk)


if __name__ == "__main__":
    main()
