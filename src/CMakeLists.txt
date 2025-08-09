# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

find_package(Rcpp REQUIRED)
find_package(RcppEigen REQUIRED)
find_package(hictk REQUIRED)

add_library(hictkR)
target_sources(
  hictkR
  PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/hictkr.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/hictkr_file.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/hictkr_multi_resolution_file.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/hictkr_singlecell_file.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/hictkr_validation.cpp"
)

target_link_libraries(
  hictkR
  PUBLIC
    hictk::libhictk
    rcpp
    rcpp_eigen
)
