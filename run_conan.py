#!/usr/bin/env python3

# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import subprocess as sp
import shutil
import os
import sys
import re


def find_conan():
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError(
            "Unable to find conan in your PATH.\n"
            "Please install conan: https://conan.io/downloads"
        )

    return conan


def run_conan_profile_detect_windows(env):
    assert os.name == "nt"

    cc = env.get("CC")
    gcc_version = sp.check_output([cc, "-dumpversion"]).decode("ascii")
    gcc_version = re.search(r"^\d+", gcc_version).group(0)

    profile = [
        "[settings]",
        "build_type=Release",
        "compiler=gcc",
        "compiler.cppstd=gnu17",
        f"compiler.version={gcc_version}",
        "os=Windows",
    ]

    conan_profile = os.path.join(
        env.get("CONAN_HOME", os.path.join(env.get("HOME"), ".conan2")),
        "profiles",
        "default",
    )

    os.makedirs(os.path.dirname(conan_profile), exist_ok=True)
    with open(conan_profile, "w") as f:
        print("\n".join(profile), file=f)


def run_conan_profile_detect(conan, env):
    if os.name == "nt":
        run_conan_profile_detect_windows(env)
        return

    sp.run([conan, "profile", "detect"], stdout=sp.DEVNULL, env=env)

    conan_profile = os.path.join(
        env.get("CONAN_HOME", os.path.join(env.get("HOME"), ".conan2")),
        "profiles",
        "default",
    )
    with open(conan_profile) as f:
        for line in f:
            print(line, file=sys.stderr)


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

    print("CONAN_HOME=" + env.get("CONAN_HOME", ""), file=sys.stderr)
    print("CC=" + env.get("CC", ""), file=sys.stderr)
    print("CXX=" + env.get("CXX", ""), file=sys.stderr)

    run_conan_profile_detect(conan, env)
    run_conan_install(conan, env)
    print(conandeps_mk)


if __name__ == "__main__":
    main()
