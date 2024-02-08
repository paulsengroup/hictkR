#!/usr/bin/env python

# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import os
import platform
import re
import shutil
import subprocess as sp
import sys


"""
This script takes care of generating a valid conan profile and running conan install.
Most of the complexity is due to Windows, as in this case we must use the compilers provided by the Rtools package.
This means that:
- We need to figure out Rtools' home folder
- Inject the several bin folders into PATH
- Detect compiler and cmake version
- Make conan use the msys2 toolchain installed by Rtools
"""


def find_conan() -> str:
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError(
            "Unable to find conan in your PATH.\n"
            "Please install conan: https://conan.io/downloads"
        )

    return conan


def get_conan_home() -> str:
    return os.environ.get(
        "CONAN_HOME", os.path.join(os.path.expanduser("~"), ".conan2")
    )


def get_rtools_home() -> str:
    res = sp.check_output(
        ["Rscript", "-e", "package_version(R.version)"], stderr=sp.DEVNULL
    ).decode("utf-8")
    matches = re.search(r"(\d+\.\d+).\d+", res)
    if not matches:
        raise RuntimeError("Unable to infer R version")

    r_version = matches.group(1).replace(".", "")

    rtools_home = os.path.join("C:\\", f"rtools{r_version}")

    if not os.path.exists(rtools_home):
        raise RuntimeError("Unable to find RTOOLS_HOME at: " + rtools_home)

    return rtools_home


def get_path_as_r() -> str:
    res = sp.check_output(
        ["Rscript", "-e", "Sys.getenv('PATH')"], stderr=sp.DEVNULL
    ).decode("utf-8")
    matches = re.search(r"\"(.*)\"", res, re.MULTILINE)
    if not matches:
        return ""

    path = [os.path.normpath(p) for p in matches.group(1).split(";")]

    rtools_home = get_rtools_home()

    path = [
        os.path.join(rtools_home, "usr", "bin"),
        os.path.join(rtools_home, "mingw64", "bin"),
    ] + path

    return ";".join(path)


def r_which(program: str) -> str:
    res = sp.check_output(
        ["Rscript", "-e", f'Sys.which("{program}")'], stderr=sp.DEVNULL
    ).decode("utf-8")

    matches = re.search(r"\n\"(.*)\"", res, re.MULTILINE)
    if not matches:
        return ""

    return os.path.normpath(matches.group(1))


def find_cc():
    cc = r_which("gcc")

    if cc == "":
        cc = r_which("clang")

    if cc == "":
        raise RuntimeError("Unable to find a gcc or clang in your PATH")

    return os.path.realpath(cc)


def find_cxx():
    cxx = r_which("g++")

    if cxx == "":
        cxx = r_which("clang++")

    if cxx == "":
        raise RuntimeError("Unable to find a g++ or clang++ in your PATH")

    return os.path.realpath(cxx)


def get_cc_version(cc) -> str:
    cc_version = sp.check_output([cc, "-dumpversion"]).decode("ascii")
    return re.search(r"^\d+", cc_version).group(0)


def get_cmake_version(env) -> str:
    res = sp.check_output(["cmake", "--version"], env=env).decode("utf-8")
    matches = re.search(r"(\d+\.\d+.\d+)", res)

    if not matches:
        raise RuntimeError("Unable to infer cmake version")

    return matches.group(1)


def get_arch() -> str:
    return platform.uname()[4].lower().replace("amd64", "x86_64")


def run_conan_profile_detect_windows(env):
    assert os.name == "nt"

    env["PATH"] = get_path_as_r()

    arch = get_arch()
    cc = find_cc()
    cxx = find_cxx()
    cc_version = get_cc_version(cc)
    cmake_version = get_cmake_version(env)

    env["CC"] = cc
    env["CXX"] = cxx

    # HDF5, szip and zlib come with Rtools, and using the version from Conan causes
    # weird link errors that are difficult to address.
    # So we claim that hdf4/1.14.3 is available as a system library (even though
    # a different version is likely installed) and call it a day
    profile = [
        "[settings]",
        f"arch={arch}",
        "build_type=Release",
        "compiler=gcc",
        "compiler.cppstd=17",
        f"compiler.version={cc_version}",
        "os=Windows",
        "[buildenv]",
        f"PATH='" + env["PATH"] + "'",
        "[platform_requires]",
        "hdf5/1.14.3",
        "[platform_tool_requires]",
        f"cmake/{cmake_version}",
    ]

    conan_profile = os.path.join(
        get_conan_home(),
        "profiles",
        "default",
    )

    os.makedirs(os.path.dirname(conan_profile), exist_ok=True)
    with open(conan_profile, "w") as f:
        print("\n".join(profile), file=f, end="")


def run_conan_profile_detect(conan, env):
    if os.name == "nt":
        run_conan_profile_detect_windows(env)
        return

    sp.run([conan, "profile", "detect"], stdout=sp.DEVNULL, env=env)

    conan_profile = os.path.join(
        env.get("CONAN_HOME", os.path.join(os.path.expanduser("~"), ".conan2")),
        "profiles",
        "default",
    )
    with open(conan_profile) as f:
        for line in f:
            print(line, file=sys.stderr)


def run_conan_install(conan, env):
    conanfile = os.path.join("..", "conanfile.txt")

    sp.check_call(
        [
            conan,
            "install",
            conanfile,
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

    conan_home = get_conan_home()
    if conan_home is not None:
        os.makedirs(conan_home, exist_ok=True)

    run_conan_profile_detect(conan, env)
    run_conan_install(conan, env)
    print(conandeps_mk)


if __name__ == "__main__":
    main()
