#!/usr/bin/env python

# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import argparse
import os
import pathlib
import platform
import re
import shutil
import subprocess as sp
import sys
from typing import Optional

"""
This script takes care of generating a valid conan profile and running conan install.
Most of the complexity is due to Windows, as in this case we must use the compilers provided by the Rtools package.
This means that:
- We need to figure out Rtools' home folder
- Inject the several bin folders into PATH
- Detect compiler and cmake version
- Make conan use the msys2 toolchain installed by Rtools
"""


def make_cli() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser()

    cli.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Run the script even if conandeps.mk already exists.",
    )

    return cli


def find_conan() -> pathlib.Path:
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError("Unable to find conan in your PATH.\nPlease install conan: https://conan.io/downloads")

    conan = pathlib.Path(conan).absolute()
    version = sp.check_output([conan, "--version"])
    print(f'found {version} at "{conan}"', file=sys.stderr)

    return conan


def get_conan_home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("CONAN_HOME", pathlib.Path().home() / ".conan2"))


def get_rtools_home() -> pathlib.Path:
    res = sp.check_output(["Rscript", "-e", "package_version(R.version)"], stderr=sp.DEVNULL).decode("utf-8")
    matches = re.search(r"(\d+\.\d+).\d+", res)
    if not matches:
        raise RuntimeError("Unable to infer R version")

    r_version = matches.group(1).replace(".", "")
    rtools_string = f"rtools{r_version}"

    rtools_home = pathlib.Path("C:\\") / rtools_string
    for p in get_path_as_r(add_rtools=False).split(";"):
        if rtools_string in p:
            matches = re.search(rf"^(.*{rtools_string})", p)
            if matches:
                rtools_home = pathlib.Path(matches.group(1))
                break

    if not rtools_home.exists():
        raise RuntimeError(f"Unable to find RTOOLS_HOME at: {rtools_home}")

    print(f'Found Rtools at "{rtools_home}"', file=sys.stderr)

    return rtools_home


def get_path_as_r(add_rtools: bool = True) -> str:
    res = sp.check_output(["Rscript", "-e", "Sys.getenv('PATH')"], stderr=sp.DEVNULL).decode("utf-8")
    matches = re.search(r"\"(.*)\"", res, re.MULTILINE)
    if not matches:
        return ""

    path = [pathlib.Path(p).resolve() for p in matches.group(1).split(";")]

    if add_rtools:
        rtools_home = get_rtools_home()

        path = [
            rtools_home / "usr" / "bin",
            rtools_home / "mingw64" / "bin",
        ] + path

    return ";".join(str(p) for p in path)


def r_which(program: str) -> Optional[pathlib.Path]:
    res = sp.check_output(["Rscript", "-e", f'Sys.which("{program}")'], stderr=sp.DEVNULL).decode("utf-8")

    matches = re.search(r"\n\"(.*)\"", res, re.MULTILINE)
    if not matches:
        return None

    return pathlib.Path(matches.group(1)).resolve()


def find_cc() -> pathlib.Path:
    cc = r_which("gcc")

    if cc == "":
        cc = r_which("clang")

    if cc == "":
        raise RuntimeError("Unable to find a gcc or clang in your PATH")

    return cc.resolve()


def find_cxx() -> pathlib.Path:
    cxx = r_which("g++")

    if cxx == "":
        cxx = r_which("clang++")

    if cxx == "":
        raise RuntimeError("Unable to find a g++ or clang++ in your PATH")

    return cxx.resolve()


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

    env["PATH"] = str(get_path_as_r())

    arch = get_arch()
    cc = find_cc()
    cxx = find_cxx()
    cc_version = get_cc_version(cc)
    cmake_version = get_cmake_version(env)

    env["CC"] = str(cc)
    env["CXX"] = str(cxx)

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
        "hdf5/1.14.5",
        "[platform_tool_requires]",
        f"cmake/{cmake_version}",
    ]

    conan_profile = get_conan_home() / "profiles" / "hictkR"
    conan_profile.parent.mkdir(exist_ok=True)
    with conan_profile.open("w") as f:
        print("\n".join(profile), file=f, end="")


def run_conan_profile_detect(conan, env):
    if os.name == "nt":
        run_conan_profile_detect_windows(env)
        return

    sp.check_call(
        [conan, "profile", "detect", "--name", "hictkR", "--force"],
        stdout=sp.DEVNULL,
        env=env,
    )

    conan_profile = pathlib.Path(env.get("CONAN_HOME", pathlib.Path().home() / ".conan2")) / "profiles" / "hictkR"
    with conan_profile.open() as f:
        for line in f:
            print(line, file=sys.stderr, end="")


def run_conan_install(conan, env):
    hictk_conanfile = pathlib.Path().cwd().parent / "hictk.conanfile.py"
    hictkR_conanfile = pathlib.Path().cwd().parent / "conanfile.txt"
    assert hictk_conanfile.exists()
    assert hictkR_conanfile.exists()

    sp.check_call(
        [
            conan,
            "create",
            hictk_conanfile,
            "--profile:all=hictkR",
            "--settings=build_type=Release",
            "--settings=compiler.cppstd=17",
            "--build=missing",
            "--update",
        ],
        stdout=sp.DEVNULL,
        env=env,
    )

    sp.check_call(
        [
            conan,
            "install",
            hictkR_conanfile,
            "--profile:all=hictkR",
            "--settings=build_type=Release",
            "--settings=compiler.cppstd=17",
            "--output-folder=conan-staging",
            "--build=never",
            "--generator=MakeDeps",
            "--generator=CMakeDeps",
        ],
        stdout=sp.DEVNULL,
        env=env,
    )


def main():
    args = make_cli().parse_args()

    conan = find_conan()
    pwd = pathlib.Path().cwd()

    env = os.environ.copy()

    conandeps_mk = pwd / "conan-staging" / "conandeps.mk"

    if args.force:
        if conandeps_mk.parent.exists():
            shutil.rmtree(conandeps_mk.parent)

    if conandeps_mk.exists():
        print(conandeps_mk)
        return

    conan_home = get_conan_home()
    if conan_home is not None:
        conan_home.mkdir(parents=True, exist_ok=True)

    run_conan_profile_detect(conan, env)
    run_conan_install(conan, env)

    if not conandeps_mk.is_file():
        raise RuntimeError(f"failed to create {conandeps_mk} file!")

    print(conandeps_mk)


if __name__ == "__main__":
    main()
