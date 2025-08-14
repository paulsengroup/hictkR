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

find_package(Rcpp REQUIRED)
find_package(RcppEigen REQUIRED)
find_package(hictk REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Arrow REQUIRED)

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
  PRIVATE
    Arrow::arrow_static
    Eigen3::Eigen
    hictk::libhictk
    rcpp
    rcpp_eigen
)
