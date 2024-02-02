# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

find_package(Rcpp REQUIRED)
find_package(hictk REQUIRED)

add_library(hictkR)
target_sources(hictkR PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/hictkr_file.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/hictkr_module.cpp")
target_link_libraries(hictkR PUBLIC hictk::libhictk rcpp)
