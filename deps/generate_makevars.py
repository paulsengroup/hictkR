#!/usr/bin/env python

# Copyright (C) 2025 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import argparse
import functools
import json
import logging
import os
import pathlib
import platform
import re
import shutil
import subprocess as sp
import sys
import tempfile
import textwrap
import venv
from typing import Dict, Tuple

type EnvDict = Dict[str, str]


def make_cli() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        "Generate a Makevars file suitable to build hictkR by linking to third-party dependencies built using Conan."
    )

    cli.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Run the script even if Makevars already exists (default: %(default)s).",
    )
    cli.add_argument(
        "--workdir",
        type=pathlib.Path,
        default=pathlib.Path().cwd(),
        help="Working directory (default: %(default)s).",
    )
    cli.add_argument(
        "--no-venv",
        action="store_true",
        default=False,
        help="Do not run commands inside an ephemeral venv (default: %(default)s).",
    )

    return cli


@functools.cache
def find_conan() -> pathlib.Path:
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError("Unable to find conan in your PATH.\nPlease install conan: https://conan.io/downloads")

    conan = pathlib.Path(conan).absolute()
    version = sp.check_output([conan, "--version"])
    logging.info('found %s at "%s"', version, conan)

    return conan


@functools.cache
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

    logging.info('Found Rtools at "%s"', rtools_home)

    return rtools_home


@functools.cache
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


@functools.cache
def r_which(program: str, resolve: bool = True) -> pathlib.Path | None:
    res = sp.check_output(["Rscript", "-e", f'Sys.which("{program}")'], stderr=sp.DEVNULL).decode("utf-8")

    matches = re.search(r"\n\"(.*)\"", res, re.MULTILINE)
    if not matches:
        return None

    exe = pathlib.Path(matches.group(1))
    if resolve:
        exe = exe.resolve()

    return exe


@functools.cache
def find_cc() -> pathlib.Path:
    for name in (os.getenv("CC", "clang"), "clang", "gcc", "cc"):
        cc = r_which(name, resolve=False)
        if cc is not None:
            return cc

    raise RuntimeError("Unable to find a gcc or clang in your PATH")


@functools.cache
def find_cxx() -> pathlib.Path:
    for name in (os.getenv("CXX", "clang++"), "clang++", "g++", "c++"):
        cxx = r_which(name, resolve=False)
        if cxx is not None:
            return cxx

    raise RuntimeError("Unable to find a g++ or clang++ in your PATH")


@functools.cache
def cxx_flags_rcpp() -> str:
    return sp.check_output(["Rscript", "-e", "Rcpp:::CxxFlags()"], stderr=sp.DEVNULL).decode("utf-8")


@functools.cache
def get_cc_version(cc) -> str:
    cc_version = sp.check_output([cc, "-dumpversion"]).decode("ascii")
    return re.search(r"^\d+", cc_version).group(0)


def get_cmake_version(env: EnvDict) -> str:
    res = sp.check_output(["cmake", "--version"], env=env).decode("utf-8")
    matches = re.search(r"(\d+\.\d+.\d+)", res)

    if not matches:
        raise RuntimeError("Unable to infer cmake version")

    return matches.group(1)


@functools.cache
def get_arch() -> str:
    return platform.uname()[4].lower().replace("amd64", "x86_64")


def compile_and_check_output(source: str, tmpdir: pathlib.Path) -> str:
    prefix = hash(source)
    src_file = tmpdir / f"{prefix}.cpp"
    test_program = tmpdir / f"{prefix}.bin"

    try:
        src_file.write_text(source)

        cmd = [find_cxx(), src_file, "-o", test_program, "-std=c++17", "-O0"]
        res = sp.check_output(cmd)

        return res.decode("utf-8")

    finally:
        src_file.unlink(missing_ok=True)
        test_program.unlink(missing_ok=True)


def detect_hdf5_version(tmpdir: pathlib.Path) -> str:
    compile_and_check_output(
        source=textwrap.dedent(
            """
            #include <H5public.h>
            #include <cstdio>
            #include <cstdlib>

            int main() {
              printf("%d.%d.%d\\n", int{H5_VERS_MAJOR}, int{H5_VERS_MINOR}, int{H5_VERS_RELEASE});
              return EXIT_SUCCESS;
            }
            """
        ),
        tmpdir=tmpdir,
    )


def detect_zlib_version(tmpdir: pathlib.Path) -> str:
    compile_and_check_output(
        source=textwrap.dedent(
            """
            #include <cstdio>
            #include <cstdlib>
            #include <zlib.h>

            int main() {
            printf("%d.%d.%d\\n", int{ZLIB_VER_MAJOR}, int{ZLIB_VER_MINOR}, int{ZLIB_VER_REVISION});
            return EXIT_SUCCESS;
            }
            """
        ),
        tmpdir=tmpdir,
    )


def run_conan_profile_detect_windows(tmpdir: pathlib.Path, env: EnvDict):
    assert platform.system() == "Windows"

    env["PATH"] = str(get_path_as_r())

    arch = get_arch()
    cc_version = get_cc_version(env["CC"])
    cmake_version = get_cmake_version(env)

    # HDF5 and zlib come with Rtools, and using the version from Conan causes
    # weird link errors that are difficult to address.
    # So we override the version in the conan profile
    profile = [
        "[settings]",
        f"arch={arch}",
        "build_type=Release",
        "compiler=gcc",
        "compiler.cppstd=17",
        f"compiler.version={cc_version}",
        "os=Windows",
        "[buildenv]",
        "PATH='" + env["PATH"] + "'",
        "[platform_requires]",
        f"hdf5/{detect_hdf5_version(tmpdir)}",
        f"zlib/{detect_zlib_version(tmpdir)}",
        "[platform_tool_requires]",
        f"cmake/{cmake_version}",
        "[replace_requires]",
        f"hdf5/*: hdf5/{detect_hdf5_version(tmpdir)}",
        f"zlib/*: zlib/{detect_zlib_version(tmpdir)}",
    ]

    conan_profile = pathlib.Path(env.get("CONAN_HOME")) / "profiles" / "hictkR"
    conan_profile.parent.mkdir(exist_ok=True)
    with conan_profile.open("w") as f:
        print("\n".join(profile), file=f, end="")


def run_conan_profile_detect(tmpdir: pathlib.Path, env: EnvDict):
    env = env.copy()

    env["CC"] = str(find_cc())
    env["CXX"] = str(find_cxx())

    if platform.system() == "Windows":
        run_conan_profile_detect_windows(tmpdir, env)
        return

    sp.check_call(
        ["conan", "profile", "detect", "--name", "hictkR", "--force"],
        stdout=sys.stderr,
        env=env,
    )

    conan_profile = pathlib.Path(env.get("CONAN_HOME")) / "profiles" / "hictkR"

    logging.info("\n%s", conan_profile.read_text())


@functools.cache
def extract_hictk_version(conanfile: pathlib.Path) -> str:
    res = sp.check_output(["conan", "inspect", conanfile, "--format=json"]).decode("utf-8")
    metadata = json.loads(res)

    if "version" not in metadata:
        raise RuntimeError(f"Unable to extract hictk's version from {conanfile}!")

    return str(metadata["version"])


def run_conan_install(
    conanfile: pathlib.Path,
    tmpdir: pathlib.Path,
    env: EnvDict,
) -> str:
    assert conanfile.is_file()
    assert tmpdir.is_dir()

    env = env.copy()
    env["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5"

    default_options = [
        "--profile:all=hictkR",
        "--settings=build_type=Release",
        "--settings=compiler.cppstd=17",
    ]

    conan_create_opts = default_options + [
        "--build=missing",
        "--update",
    ]

    conan_install_opts = default_options + [
        f"--requires=hictk/{extract_hictk_version(conanfile)}",
        f"--output-folder={tmpdir}",
        "--build=never",
        "--generator=MakeDeps",
    ]

    sp.check_call(
        ["conan", "create", conanfile] + conan_create_opts,
        stdout=sys.stderr,
        env=env,
    )

    sp.check_call(
        ["conan", "install"] + conan_install_opts,
        stdout=sys.stderr,
        env=env,
    )

    conandeps_mk = tmpdir / "conandeps.mk"
    if not conandeps_mk.is_file():
        raise RuntimeError(f"failed to create {conandeps_mk} file!")

    return conandeps_mk.read_text(encoding="utf-8")


def detect_filesystem_link_flag(tmpdir: pathlib.Path) -> str | None:

    src_file = tmpdir / "filesystem_test.cpp"
    test_program = tmpdir / "test.bin"

    src_file.write_text(
        textwrap.dedent(
            """
            #include <filesystem>

            int main() {
                return std::filesystem::path{}.empty() == false;
            }
            """
        )
    )

    def try_compile(*args) -> bool:
        cxx = find_cxx()
        env = os.environ.copy()
        env["CCACHE_DISABLE"] = "1"

        cmd = [cxx, src_file, "-o", test_program, "-std=c++17", *args]

        res = sp.run(cmd, env=env, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        if res.returncode != 0:
            return False

        res = sp.run([test_program])

        return res.returncode == 0

    try:

        if try_compile():
            return None

        for flag in ("-lc++fs", "-lstdc++fs"):
            if try_compile(flag):
                return flag

        raise RuntimeError(f"{find_cxx().resolve()} cannot compile a simple program using the std::filesystem library")

    finally:
        src_file.unlink(missing_ok=True)
        test_program.unlink(missing_ok=True)


def generate_makevars(
    dest: pathlib.Path,
    tmpdir: pathlib.Path,
    conandeps_mk: str,
):
    cc = find_cc()
    cxx = find_cxx()
    cxx_flags = cxx_flags_rcpp()

    makevars = textwrap.dedent(
        f"""
        PWD := $(shell pwd)
        TMPDIR := PWD

        export CC := {cc}
        export CXX := {cxx}
        export CXX17 := {cxx}

        ### BEGINNING OF conandeps.mk
        {conandeps_mk}
        ### END OF conandeps.mk

        CXX_STD := CXX17

        PKG_CPPFLAGS := $(addprefix -isystem ,$(CONAN_INCLUDE_DIRS))
        PKG_CPPFLAGS := $(PKG_CPPFLAGS) $(addprefix -D ,$(CONAN_DEFINES))
        PKG_CPPFLAGS := $(PKG_CPPFLAGS) {cxx_flags}

        PKG_LIBS := $(addprefix -L ,$(CONAN_LIB_DIRS))
        PKG_LIBS := $(PKG_LIBS) $(addprefix -l,$(CONAN_LIBS))
        PKG_LIBS := $(PKG_LIBS) $(addprefix -l,$(CONAN_SYSTEM_LIBS))
        """
    )

    filesystem_link_flags = detect_filesystem_link_flag(tmpdir)
    if filesystem_link_flags is not None:
        makevars += f"PKG_LIBS := $(PKG_LIBS) {filesystem_link_flags}"

    if platform.system() == "Windows":
        # These libraries come with Rtools, and installing them with Conan leads to link errors that are difficult to address
        makevars += "PKG_LIBS := $(PKG_LIBS) -lhdf5 -lz -lsz"
    else:
        makevars += "PKG_CPPFLAGS := $(PKG_CPPFLAGS) $(addprefix -isystem ,$(CONAN_INCLUDE_DIRS_HDF5_HDF5_C))"

    dest.write_text(makevars, newline="\n")


def get_or_init_conan_home(env: EnvDict | None) -> pathlib.Path:
    if env is None:
        env = os.environ.copy()

    conan_home = env.get("HICTKR_CONAN_HOME")
    if conan_home is None:
        default_conan_home = pathlib.Path().home() / ".conan2"
        conan_home = env.get("CONAN_HOME", default_conan_home)

    conan_home = pathlib.Path(conan_home).absolute()
    conan_home.mkdir(exist_ok=True, parents=True)

    return conan_home


def setup_venv(tmpdir: pathlib.Path) -> Tuple[pathlib.Path, EnvDict]:
    venv_path = tmpdir / "venv"
    logging.info('creating venv under "%s"...', venv_path)
    venv.create(venv_path, with_pip=True, upgrade_deps=True)

    env = os.environ.copy()
    path = env["PATH"]

    bin_path = venv_path / "bin"
    if bin_path.exists():
        env["PATH"] = f"{bin_path}:{path}"
    else:
        bin_path = venv_path / "Scripts"
        assert bin_path.exists()
        env["PATH"] = f"{bin_path};{path}"

    sp.check_call(
        ["pip", "install", "conan>=2", "cmake>=3.25"],
        stdout=sys.stderr,
        env=env,
    )

    return venv_path, env


def setup_logger(level: str = "INFO"):
    fmt = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(format=fmt)
    logging.getLogger().setLevel(level)


def main():
    args = make_cli().parse_args()

    workdir = args.workdir

    makevars_file = workdir / "src" / "Makevars"

    if args.force:
        makevars_file.unlink(missing_ok=True)

    if makevars_file.exists():
        logging.debug("\n%s", makevars_file.read_text())
        logging.info('found existing Makevars file at "%s"!', makevars_file.resolve())
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = pathlib.Path(tmpdir)
        if args.no_venv:
            logging.info("skipping venv creation...")
            env: EnvDict = os.environ.copy()
        else:
            _, env = setup_venv(tmpdir)

        conan_home = get_or_init_conan_home(env)

        logging.info("CONAN_HOME=%s", conan_home)
        env["CONAN_HOME"] = str(conan_home)
        env["TMPDIR"] = str(tmpdir.absolute())

        run_conan_profile_detect(tmpdir, env)
        conandeps_mk = run_conan_install(workdir / "deps" / "conanfile.py", tmpdir, env)

        generate_makevars(makevars_file, tmpdir, conandeps_mk)

        logging.debug("\n%s", makevars_file.read_text())
        logging.info('Makevars file has been written to "%s"...', makevars_file.resolve())


if __name__ == "__main__":
    setup_logger()
    main()
