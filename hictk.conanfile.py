# Copyright (C) 2025 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import os.path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.scm import Version

required_conan_version = ">=1.50.0"


class HictkConan(ConanFile):
    name = "hictk"
    version = "2.1.2"
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
                    "sha256": "6a3d5e30e980d31b99b8be66407d6e54539a6b07f51eed60e60b5fcd297e6e57",
                },
            }
        }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "apple-clang": "11",
            "clang": "7",
            "gcc": "8",
            "Visual Studio": "16",
            "msvc": "192",
        }

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # self.requires("arrow/19.0.1#f6937fd566ecbec1eab37b40e292dfec")
        # self.requires("boost/1.87.0#0c087f18c4e6487235dd10480613cbb5", force=True)
        self.requires("bshoshany-thread-pool/5.0.0#d94da300363f0c35b8f41b2c5490c94d")
        self.requires("concurrentqueue/1.0.4#1e48e1c712bcfd892087c9c622a51502")
        self.requires("eigen/3.4.0#2e192482a8acff96fe34766adca2b24c")
        self.requires("fast_float/8.0.0#edda0315516b2f1e7835972fdf5fc5ca")
        self.requires("fmt/11.2.0#579bb2cdf4a7607621beea4eb4651e0f", force=True)
        self.requires("hdf5/1.14.5#51799cda2ba7acaa74c9651dea284ac4", force=True)
        self.requires("highfive/2.10.0#c975a16d7fe3655c173f8a9aab16b416")
        self.requires("libdeflate/1.23#4994bea7cf7e93789da161fac8e26a53")
        self.requires("parallel-hashmap/2.0.0#82acae64ffe2693fff5fb3f9df8e1746")
        self.requires("readerwriterqueue/1.0.6#aaa5ff6fac60c2aee591e9e51b063b83")
        self.requires("span-lite/0.11.0#519fd49fff711674cfed8cd17d4ed422")
        self.requires("spdlog/1.15.1#92e99f07f134481bce4b70c1a41060e7")
        self.requires("zstd/1.5.7#fde461c0d847a22f16d3066774f61b11", force=True)

    def package_id(self):
        self.info.clear()

    def validate(self):
        if self.settings.get_safe("compiler.cppstd"):
            check_min_cppstd(self, self._min_cppstd)

        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler))
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

        if self.info.options.get_safe("with_arrow"):
            arrow = self.dependencies["arrow"]
            if not arrow.options.compute:
                raise ConanInvalidConfiguration(f"{self.ref} requires the dependency option arrow/*:compute=True")

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
        tc.variables["HICTK_WITH_ARROW"] = "OFF"
        tc.variables["HICTK_WITH_EIGEN"] = "ON"
        tc.generate()

        cmakedeps = CMakeDeps(self)
        cmakedeps.generate()

    def build(self):
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

        # self.cpp_info.defines.append("HICTK_WITH_ARROW")
        self.cpp_info.defines.append("HICTK_WITH_EIGEN")

    def configure(self):
        if self.settings.compiler in ["clang", "gcc"] and self.settings.os == "Linux":
            self.settings.compiler.libcxx = "libstdc++11"

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
