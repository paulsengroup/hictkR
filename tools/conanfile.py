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


import os.path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    export_conandata_patches,
    get,
    rmdir,
)
from conan.tools.scm import Version

required_conan_version = ">=2.0"


class HictkConan(ConanFile):
    name = "hictk"
    version = "2.1.4"
    description = "Blazing fast toolkit to work with .hic and .cool files"
    license = "MIT"
    url = "https://github.com/paulsengroup/hictkR"
    homepage = "https://github.com/paulsengroup/hictk"
    topics = "hictk", "bioinformatics", "hic"
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def __init__(self, *args, **kwargs):
        super(HictkConan, self).__init__(*args, **kwargs)
        self.conan_data = {
            "sources": {
                HictkConan.version: {
                    "url": f"https://github.com/paulsengroup/hictk/archive/refs/tags/v{HictkConan.version}.tar.gz",
                    "sha256": "3a0030425176dacc25c20afc6fedb5dfbbc3c1a67f773be11ac77d7fa6b7efde",
                },
            },
            "patches": {
                "2.1.4": [
                    {
                        "patch_file": "patches/hictk_v2.1.4_eigen_include.patch",
                        "patch_type": "portabiliy",
                        "patch_description": "Support including Eigen headers located under eigen3/",
                    }
                ]
            },
        }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("arrow/21.0.0#228b4b648a5100809cd7d17451d87233")
        self.requires("bshoshany-thread-pool/5.0.0#d94da300363f0c35b8f41b2c5490c94d")
        self.requires("concurrentqueue/1.0.4#1e48e1c712bcfd892087c9c622a51502")
        self.requires("eigen/3.4.90-unstable git.2025.08.15#b407f03f085cdb246f6bcbadd84fe9db")
        self.requires("fast_float/8.0.2#846ad0ebab16bc265c511095c3b490e9")
        self.requires("fmt/11.2.0#579bb2cdf4a7607621beea4eb4651e0f", force=True)
        self.requires("hdf5/1.14.6#6f1acd01d23d00735fe97300f4d5980c", force=True)
        self.requires("highfive/2.10.0#75c849a0d940b2d4dae6055915132690")
        self.requires("libdeflate/1.23#4994bea7cf7e93789da161fac8e26a53")
        self.requires("parallel-hashmap/2.0.0#82acae64ffe2693fff5fb3f9df8e1746")
        self.requires("readerwriterqueue/1.0.6#aaa5ff6fac60c2aee591e9e51b063b83")
        self.requires("span-lite/0.11.0#519fd49fff711674cfed8cd17d4ed422")
        self.requires("spdlog/1.15.3#3ca0e9e6b83af4d0151e26541d140c86")
        self.requires("zstd/1.5.7#fde461c0d847a22f16d3066774f61b11", force=True)

    def package_id(self):
        self.info.clear()

    def export_sources(self):
        export_conandata_patches(self)

    def validate(self):
        check_min_cppstd(self, 17)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.25]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["HICTK_BUILD_BENCHMARKS"] = "OFF"
        tc.variables["HICTK_BUILD_EXAMPLES"] = "OFF"
        tc.variables["HICTK_BUILD_TOOLS"] = "OFF"
        tc.variables["HICTK_ENABLE_GIT_VERSION_TRACKING"] = "OFF"
        tc.variables["HICTK_ENABLE_TELEMETRY"] = "OFF"
        tc.variables["HICTK_ENABLE_TESTING"] = "OFF"
        tc.variables["HICTK_ENABLE_FUZZY_TESTING"] = "OFF"
        tc.variables["HICTK_WITH_ARROW"] = "ON"
        tc.variables["HICTK_WITH_EIGEN"] = "ON"
        tc.generate()

        cmakedeps = CMakeDeps(self)
        cmakedeps.generate()

    def build(self):
        apply_conandata_patches(self)

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property("cmake_file_name", "hictk")
        self.cpp_info.set_property("cmake_target_name", "hictk::libhictk")

        self.cpp_info.defines.append("HICTK_WITH_ARROW")
        self.cpp_info.defines.append("HICTK_WITH_EIGEN")

    def configure(self):
        self.options["arrow"].compute = True
        self.options["arrow"].filesystem_layer = False
        self.options["arrow"].parquet = False
        self.options["arrow"].with_boost = False
        self.options["arrow"].with_re2 = False
        self.options["arrow"].with_thrift = False
        self.options["arrow"].with_zlib = False
        self.options["fmt"].header_only = True
        self.options["hdf5"].enable_cxx = False
        self.options["hdf5"].hl = False
        self.options["hdf5"].threadsafe = False
        self.options["hdf5"].parallel = False
        self.options["highfive"].with_boost = False
        self.options["highfive"].with_eigen = False
        self.options["highfive"].with_opencv = False
        self.options["highfive"].with_xtensor = False
        self.options["spdlog"].header_only = True
        self.options["zstd"].build_programs = False
