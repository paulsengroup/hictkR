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


mcool_file <- test_path("..", "data", "cooler_test_file.mcool")

test_that("MultiResFile: path accessor", {
  f <- MultiResFile(mcool_file)
  expect_equal(f$path, mcool_file)
})

test_that("MultiResFile: chromosomes accessor", {
  path1 <- mcool_file
  path2 <- test_path("..", "data", "chromosomes.tsv.gz")

  chroms <- MultiResFile(path1)$chromosomes
  expected_chroms <- read.csv(path2, sep = "\t")
  expect_equal(chroms, expected_chroms)
})

test_that("MultiResFile: file resolutions accessor", {
  f <- MultiResFile(mcool_file)
  expect_equal(f$resolutions, c(100000, 1000000))
})
