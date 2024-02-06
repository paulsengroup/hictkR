#!/usr/bin/env python3

# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import subprocess as sp
import shutil
import os
import sys


def find_conan():
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError(
            "Unable to find conan in your PATH.\n"
            "Please install conan: https://conan.io/downloads"
        )

    return conan


def run_conan_profile_detect(conan, env):
    sp.run([conan, "profile", "detect"], stdout=sp.DEVNULL, env=env)


def run_conan_install(conan, env):
    sp.check_call(
        [
            conan,
            "install",
            os.path.join("..", "conanfile.txt"),
            "--settings=build_type=Release",
            "--settings=compiler.cppstd=17",
            "--output-folder=conan-staging",
            "--build=missing",
            "--update",
        ],
        stdout=sp.DEVNULL,
        env=env,
    )


def main():
    conan = find_conan()
    pwd = os.getcwd()

    env = os.environ.copy()

    conandeps_mk = os.path.join(pwd, "conan-staging", "conandeps.mk")

    if os.path.exists(conandeps_mk):
        print(conandeps_mk)
        return

    conan_home = env.get("CONAN_HOME")
    if conan_home is not None:
        os.makedirs(conan_home, exist_ok=True)

        cc = env.get("CC")

        new_cc = os.path.join(conan_home, "gcc")
        try:
            os.symlink(cc, new_cc)
        except FileExistsError:
            pass
        env["CC"] = new_cc

        cxx = env.get("CXX")
        if cxx is not None:
            new_cxx = os.path.join(conan_home, "g++")

            try:
                os.symlink(cxx, new_cxx)
            except FileExistsError:
                pass
            env["CXX"] = new_cxx

    print("CONAN_HOME=" + env.get("CONAN_HOME", ""), file=sys.stderr)
    print("CC=" + env.get("CC", ""), file=sys.stderr)
    print("CXX=" + env.get("CXX", ""), file=sys.stderr)

    run_conan_profile_detect(conan, env)
    run_conan_install(conan, env)
    print(conandeps_mk)


if __name__ == "__main__":
    main()
