#!/usr/bin/env python

# Copyright (C) 2025 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Public License as published
# by the Free Software Foundation; either version 3 of the License,
# or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Public License along
# with this library.  If not, see
# <https://www.gnu.org/licenses/>.


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


def run_rscript(
    args: str,
    env: EnvDict | None = None,
    strip_warnings: bool = True,
) -> str:
    data = sp.check_output(["Rscript", "-e", args], stderr=sp.DEVNULL, env=env).decode("utf-8")

    if not strip_warnings:
        return data

    pattern = re.compile(r"^\s*WARNING", re.IGNORECASE)
    lines = data.splitlines(keepends=True)

    return "".join(line for line in lines if not pattern.match(line))


def guess_rtools_home(major_version: str) -> pathlib.Path:
    paths = list(pathlib.Path("C:\\").glob(f"rtools{major_version}*"))
    if len(paths) == 0:
        raise RuntimeError(f"Unable to find Rtools for R {major_version}.x.x under C:\\")

    return max(paths)


@functools.cache
def get_rtools_home() -> pathlib.Path:
    major = run_rscript("suppressWarnings(cat(getRversion()$major))")
    minor = run_rscript("suppressWarnings(cat(getRversion()$minor))")

    rtools_home = pathlib.Path("C:\\") / f"rtools{major}{minor}"

    if not rtools_home.exists():
        logging.warning("Unable to find RTOOLS_HOME at: %s (major=%s, minor=%s)", rtools_home, major, minor)
        rtools_home = guess_rtools_home(major)

    assert rtools_home.exists()

    logging.info('Found Rtools at "%s"', rtools_home)

    return rtools_home


@functools.cache
def get_path_as_r(try_add_rtools: bool = True) -> str:
    res = run_rscript("suppressWarnings(cat(Sys.getenv('PATH')))")

    if res == "":
        raise RuntimeError("Failed to find the PATH environment variable")

    if not try_add_rtools:
        return res

    try:
        rtools_home = get_rtools_home()

        path = [pathlib.Path(p).resolve() for p in res.split(";")]

        def add_dir_to_path(directory: pathlib.Path):
            try:
                path.insert(0, directory.resolve(strict=True))
            except OSError as e:
                logging.warning(f"{e}: continuing anyway...")

        add_dir_to_path(rtools_home / "mingw64" / "bin")
        add_dir_to_path(rtools_home / "usr" / "bin")

        return ";".join(str(p) for p in path)
    except RuntimeError as e:
        if str(e).startswith("Unable to find Rtools"):
            logging.warning(f"{e}: continuing anyway...")
            return res

        raise


@functools.cache
def r_which(
    program: str,
    resolve: bool = True,
    raise_if_not_found: bool = True,
) -> pathlib.Path | None:
    res = run_rscript(f'suppressWarnings(cat(Sys.which("{program}")))')

    if res == "":
        if raise_if_not_found:
            raise RuntimeError(f'Unable to find "{program}" in PATH')
        return None

    exe = pathlib.Path(res)
    if resolve:
        exe = exe.resolve()

    return exe


@functools.cache
def find_cc() -> pathlib.Path:
    for name in (os.getenv("CC", "clang"), "clang", "gcc", "cc"):
        cc = r_which(name, resolve=False, raise_if_not_found=False)
        if cc is not None:
            return cc

    raise RuntimeError("Unable to find a gcc or clang in your PATH")


@functools.cache
def find_cxx() -> pathlib.Path:
    for name in (os.getenv("CXX", "clang++"), "clang++", "g++", "c++"):
        cxx = r_which(name, resolve=False, raise_if_not_found=False)
        if cxx is not None:
            return cxx

    raise RuntimeError("Unable to find a g++ or clang++ in your PATH")


@functools.cache
def cxx_flags_rcpp() -> str:
    return run_rscript("suppressWarnings(Rcpp:::CxxFlags())")


@functools.cache
def get_cc_version(cc) -> str:
    cc_version = sp.check_output([cc, "-dumpversion"]).decode("ascii")
    return re.search(r"^\d+", cc_version).group(0)


def get_cmake_version(env: EnvDict) -> str:
    if platform.system() == "Windows":
        res = sp.check_output(["cmake.exe", "--version"], env=env).decode("utf-8")
    else:
        res = sp.check_output(["cmake", "--version"], env=env).decode("utf-8")

    matches = re.search(r"^cmake version (\d+\.\d+\.\d+)", res.partition("\n")[0])

    if not matches:
        raise RuntimeError("Unable to infer cmake version")

    return matches.group(1)


def get_b2_version(env: EnvDict) -> str:
    if platform.system() == "Windows":
        res = sp.check_output(["b2.exe", "--version"], env=env).decode("utf-8")
    else:
        res = sp.check_output(["b2", "--version"], env=env).decode("utf-8")

    matches = re.search(r"^B2 (\d+\.\d+\.\d+).*$", res.partition("\n")[0])

    if not matches:
        raise RuntimeError("Unable to infer b2 version")

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

        cmd = [
            find_cxx(),
            src_file,
            "-o",
            test_program,
            "-std=c++17",
            "-O0",
        ]
        sp.check_call(cmd)

        res = sp.check_output(test_program)

        return res.decode("utf-8")

    finally:
        src_file.unlink(missing_ok=True)
        test_program.unlink(missing_ok=True)


def detect_hdf5_version(tmpdir: pathlib.Path) -> str:
    res = compile_and_check_output(
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

    assert res != ""
    return res


def detect_zlib_version(tmpdir: pathlib.Path) -> str:
    res = compile_and_check_output(
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
    assert res != ""
    return res


def run_conan_profile_detect_windows(tmpdir: pathlib.Path, env: EnvDict):
    assert platform.system() == "Windows"

    env = env.copy()
    env["PATH"] = str(get_path_as_r()) + ";" + env["PATH"]

    arch = get_arch()
    cc_version = get_cc_version(env["CC"])
    cmake_version = get_cmake_version(env)
    b2_version = get_b2_version(env)
    path = env["PATH"]

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
        f"PATH='{path}'",
        "[platform_requires]",
        f"hdf5/{detect_hdf5_version(tmpdir)}",
        # f"zlib/{detect_zlib_version(tmpdir)}",
        "[platform_tool_requires]",
        f"b2/{b2_version}",
        f"cmake/{cmake_version}",
        "[replace_requires]",
        f"hdf5/*: hdf5/{detect_hdf5_version(tmpdir)}",
        # f"zlib/*: zlib/{detect_zlib_version(tmpdir)}",
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
        "--conf=tools.cmake.cmaketoolchain:generator=Ninja",
    ]

    if platform.system() != "Darwin":
        default_options.append("--settings=compiler.libcxx=libstdc++11")

    conan_create_opts = default_options + [
        "--build=missing",
        "--build=hictk/*",
        "--update",
    ]

    if platform.system() != "Windows":
        conan_create_opts.append("--build=b2/*")

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
        export CC := {cc}
        export CXX := {cxx}
        export CXX17 := {cxx}

        ### BEGINNING OF conandeps.mk
        {conandeps_mk}
        ### END OF conandeps.mk

        CXX_STD = CXX17

        PKG_CPPFLAGS += $(addprefix -isystem ,$(CONAN_INCLUDE_DIRS))
        PKG_CPPFLAGS += $(addprefix -D,$(CONAN_DEFINES))
        PKG_CPPFLAGS += {cxx_flags}

        PKG_LIBS += $(addprefix -L ,$(CONAN_LIB_DIRS))
        PKG_LIBS += $(addprefix -l,$(CONAN_LIBS))
        PKG_LIBS += $(addprefix -l,$(CONAN_SYSTEM_LIBS))
        """
    )

    filesystem_link_flags = detect_filesystem_link_flag(tmpdir)
    if filesystem_link_flags is not None:
        makevars += f"PKG_LIBS += {filesystem_link_flags}\n"

    if platform.system() == "Windows":
        # These libraries come with Rtools, and installing them with Conan leads to link errors that are difficult to address
        # -lole32 is used to workaround linker errors complaining about missing __imp_CoTaskMemFree
        makevars += "PKG_LIBS += -lhdf5 -lz -lsz -lole32\n"
    else:
        makevars += "PKG_CPPFLAGS += $(addprefix -isystem ,$(CONAN_INCLUDE_DIRS_HDF5_HDF5_C))\n"

    if platform.system() == "Darwin":
        makevars += "PKG_LIBS += -Wl,-x\n"
    else:
        makevars += "PKG_LIBS += -Wl,--strip-debug\n"

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
    makevars_file.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        logging.info("Using %s as tmpdir", tmpdir)
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
        conandeps_mk = run_conan_install(workdir / "tools" / "conanfile.py", tmpdir, env)

        generate_makevars(makevars_file, tmpdir, conandeps_mk)

        logging.debug("\n%s", makevars_file.read_text())
        logging.info('Makevars file has been written to "%s"...', makevars_file.resolve())


if __name__ == "__main__":
    setup_logger()
    main()
