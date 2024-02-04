# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

cmake_minimum_required(VERSION 3.25)
cmake_policy(VERSION 3.25...3.27)
set(CMAKE_POLICY_DEFAULT_CMP0069 NEW)
set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules/")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_FIND_PACKAGE_PREFER_CONFIG)
  set(CMAKE_FIND_PACKAGE_PREFER_CONFIG ON)
endif()

project(
  hictkR
  LANGUAGES C CXX
  HOMEPAGE_URL https://github.com/paulsengroup/hictkR
  DESCRIPTION "R bindings for hictk")

include(FetchContent)
FetchContent_Declare(
  hictkR_project_options
  URL "${CMAKE_CURRENT_SOURCE_DIR}/external/project_options-v0.33.0.tar.xz"
  URL_HASH SHA256=b55dddd6c8af37c35b0bdd90d78088ef05beb423d6a56a55850e33fa3d464675
  SYSTEM)

FetchContent_MakeAvailable(hictkR_project_options)

get_property(BUILDING_MULTI_CONFIG GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(BUILDING_MULTI_CONFIG)
  if(NOT CMAKE_BUILD_TYPE)
    # Make sure that all supported configuration types have their associated conan packages available. You can reduce
    # this list to only the configuration types you use, but only if one is not forced-set on the command line for VS
    message(TRACE "Setting up multi-config build types")
    set(CMAKE_CONFIGURATION_TYPES
        Debug Release RelWithDebInfo
        CACHE STRING "Enabled build types" FORCE)
  else()
    message(TRACE "User chose a specific build type, so we are using that")
    set(CMAKE_CONFIGURATION_TYPES
        ${CMAKE_BUILD_TYPE}
        CACHE STRING "Enabled build types" FORCE)
  endif()
endif()

include("${hictkr_project_options_SOURCE_DIR}/src/DynamicProjectOptions.cmake")
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/CompilerWarnings.cmake")

set(ENABLE_CACHE_DEFAULT ON)
set(ENABLE_COMPILE_COMMANDS_SYMLINK_DEFAULT OFF)
set(ENABLE_CONAN_DEFAULT OFF)
set(ENABLE_CPPCHECK_DEFAULT OFF)
set(ENABLE_DOXYGEN_USER OFF)
set(ENABLE_DOXYGEN_DEVELOPER ON)
set(ENABLE_INTERPROCEDURAL_OPTIMIZATION_DEFAULT ON)
set(ENABLE_NATIVE_OPTIMIZATION_DEFAULT OFF)
set(ENABLE_PCH_DEFAULT OFF)

set(ENABLE_SANITIZER_ADDRESS_USER OFF)
set(ENABLE_SANITIZER_ADDRESS_DEVELOPER ON)
set(ENABLE_SANITIZER_LEAK_USER OFF)
set(ENABLE_SANITIZER_LEAK_DEVELOPER ON)
set(ENABLE_SANITIZER_UNDEFINED_BEHAVIOR_USER OFF)
set(ENABLE_SANITIZER_UNDEFINED_BEHAVIOR_DEVELOPER ON)

dynamic_project_options(
  PREFIX
  hictkR
  # CLANG_WARNINGS # Override the defaults for the CLANG warnings GCC_WARNINGS   # Override the defaults for the GCC
  CPPCHECK_OPTIONS
  --enable=performance,portability,style,warning
  --inline-suppr
  # We cannot act on a bug/missing feature of cppcheck
  --suppress=internalAstError
  # if a file does not have an internalAstError, we get an unmatchedSuppression error
  --suppress=unmatchedSuppression
  --suppress=passedByValue
  --inconclusive
  MSVC_WARNINGS
  "${MSVC_WARNINGS}"
  CLANG_WARNINGS
  "${CLANG_WARNINGS}"
  GCC_WARNINGS
  "${GCC_WARNINGS}"
  CUDA_WARNINGS
  "${CUDA_WARNINGS}")

target_compile_features(hictkR_project_options INTERFACE "cxx_std_${CMAKE_CXX_STANDARD}")

if(MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /bigobj")
endif()

add_subdirectory(src)
