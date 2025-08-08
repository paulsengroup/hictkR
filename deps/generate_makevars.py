#!/usr/bin/env python

# Copyright (C) 2025 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import argparse
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

"""
This script takes care of generating a valid conan profile and running conan install.
Most of the complexity is due to Windows, as in this case we must use the compilers provided by the Rtools package.
This means that:
- We need to figure out Rtools' home folder
- Inject the several bin folders into PATH
- Detect compiler and cmake version
- Make conan use the msys2 toolchain installed by Rtools
"""

type EnvDict = Dict[str, str]


def make_cli() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser()

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


def find_conan() -> pathlib.Path:
    conan = shutil.which("conan")
    if conan is None:
        raise RuntimeError("Unable to find conan in your PATH.\nPlease install conan: https://conan.io/downloads")

    conan = pathlib.Path(conan).absolute()
    version = sp.check_output([conan, "--version"])
    logging.info('found %s at "%s"', version, conan)

    return conan


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


def r_which(program: str, resolve: bool = True) -> pathlib.Path | None:
    res = sp.check_output(["Rscript", "-e", f'Sys.which("{program}")'], stderr=sp.DEVNULL).decode("utf-8")

    matches = re.search(r"\n\"(.*)\"", res, re.MULTILINE)
    if not matches:
        return None

    exe = pathlib.Path(matches.group(1))
    if resolve:
        exe = exe.resolve()

    return exe


def find_cc() -> pathlib.Path:
    for name in (os.getenv("CC", "cc"), "cc", "gcc", "clang"):
        cc = r_which(name, resolve=False)
        if cc is not None:
            if "ccache" in str(cc):
                return cc
            return cc.resolve()

    raise RuntimeError("Unable to find a gcc or clang in your PATH")


def find_cxx() -> pathlib.Path:
    for name in (os.getenv("CXX", "c++"), "c++", "g++", "clang++"):
        cxx = r_which(name, resolve=False)
        if cxx is not None:
            if "ccache" in str(cxx):
                return cxx
            return cxx.resolve()

    raise RuntimeError("Unable to find a g++ or clang++ in your PATH")


def cxx_flags_rcpp() -> str:
    return sp.check_output(["Rscript", "-e", "Rcpp:::CxxFlags()"], stderr=sp.DEVNULL).decode("utf-8")


def get_cc_version(cc) -> str:
    cc_version = sp.check_output([cc, "-dumpversion"]).decode("ascii")
    return re.search(r"^\d+", cc_version).group(0)


def get_cmake_version(env: EnvDict) -> str:
    res = sp.check_output(["cmake", "--version"], env=env).decode("utf-8")
    matches = re.search(r"(\d+\.\d+.\d+)", res)

    if not matches:
        raise RuntimeError("Unable to infer cmake version")

    return matches.group(1)


def get_arch() -> str:
    return platform.uname()[4].lower().replace("amd64", "x86_64")


def run_conan_profile_detect_windows(env: EnvDict):
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

    conan_profile = pathlib.Path(env.get("CONAN_HOME")) / "profiles" / "hictkR"
    conan_profile.parent.mkdir(exist_ok=True)
    with conan_profile.open("w") as f:
        print("\n".join(profile), file=f, end="")


def run_conan_profile_detect(env: EnvDict):
    if os.name == "nt":
        run_conan_profile_detect_windows(env)
        return

    sp.check_call(
        ["conan", "profile", "detect", "--name", "hictkR", "--force"],
        stdout=sys.stderr,
        env=env,
    )

    conan_profile = pathlib.Path(env.get("CONAN_HOME")) / "profiles" / "hictkR"
    logging.info("\n%s", conan_profile.read_text())


def run_conan_install(
    conanfile: pathlib.Path,
    tmpdir: pathlib.Path,
    env: EnvDict,
) -> pathlib.Path:
    assert conanfile.is_file()
    assert tmpdir.is_dir()

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
        "--requires=hictk/[>=2.1 <2.2]",
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

    return conandeps_mk


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

        raise RuntimeError("Cannot compile a simple program using the std::filesystem library")

    finally:
        src_file.unlink()
        test_program.unlink()


def generate_makevars_unix(dest: pathlib.Path, tmpdir: pathlib.Path, conandeps_mk: pathlib.Path):
    cc = find_cc()
    cxx = find_cxx()
    cxx_flags = cxx_flags_rcpp()

    makevars = (
        textwrap.dedent(
            f"""
        PWD := $(shell pwd)
        TMPDIR := PWD

        export CC := {cc}"
        export CXX := {cxx}
        export CXX17 = $(CXX)

        ### BEGINNING OF conandeps.mk
        """
        )
        + conandeps_mk.read_text(encoding="utf-8")
        + textwrap.dedent(
            f"""
        ### END OF conandeps.mk

        CXX_STD := CXX17

        PKG_CPPFLAGS := $(addprefix -isystem ,$(CONAN_INCLUDE_DIRS))
        PKG_CPPFLAGS := $(PKG_CPPFLAGS) $(addprefix -isystem ,$(CONAN_INCLUDE_DIRS_HDF5_HDF5_C))
        PKG_CPPFLAGS := $(PKG_CPPFLAGS) $(addprefix -D ,$(CONAN_DEFINES))
        PKG_CPPFLAGS := $(PKG_CPPFLAGS) {cxx_flags}

        PKG_LIBS := $(addprefix -L ,$(CONAN_LIB_DIRS))
        PKG_LIBS := $(PKG_LIBS) $(addprefix -l,$(CONAN_LIBS))
        PKG_LIBS := $(PKG_LIBS) $(addprefix -l,$(CONAN_SYSTEM_LIBS))
        """
        )
    )

    filesystem_link_flags = detect_filesystem_link_flag(tmpdir)
    if filesystem_link_flags is not None:
        makevars += f"PKG_LIBS := $(PKG_LIBS) {filesystem_link_flags}"

    dest.write_text(makevars)


def generate_makevars_windows(dest: pathlib.Path, conandeps_mk: pathlib.Path):
    pass


def generate_makevars(dest: pathlib.Path, conandeps_mk: pathlib.Path, tmpdir: pathlib.Path):
    if os.name == "nt":
        generate_makevars_windows(dest, conandeps_mk)
    else:
        generate_makevars_unix(dest, tmpdir, conandeps_mk)


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

        run_conan_profile_detect(env)
        conandeps_mk = run_conan_install(workdir / "deps" / "conanfile.py", tmpdir, env)

        generate_makevars(makevars_file, conandeps_mk, tmpdir)

        logging.debug("\n%s", makevars_file.read_text())
        logging.info('Makevars file has been written to "%s"...', makevars_file.resolve())


if __name__ == "__main__":
    setup_logger()
    main()
