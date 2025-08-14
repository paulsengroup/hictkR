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


hic_file <- test_path("..", "data", "hic_test_file.hic")
mcool_file <- test_path("..", "data", "cooler_test_file.mcool")
scool_file <- test_path("..", "data", "cooler_test_file.scool")
cool_file <- paste(test_path("..", "data", "cooler_test_file.mcool"), "::/resolutions/100000", sep = "")

test_that("hicrkR_open: .hic", {
  expected <- class(File(hic_file, 100000))

  f <- hictkR_open(hic_file, 100000)
  expect_equal(expected, class(f))
})

test_that("hicrkR_open: .cool", {
  expected <- class(File(cool_file))

  f <- hictkR_open(cool_file)
  expect_equal(expected, class(f))

  f <- hictkR_open(mcool_file, resolution = 100000)
  expect_equal(expected, class(f))

  f <- hictkR_open(scool_file, cell = "GSM2687248_41669_ACAGTG-R1-DpnII.100000.cool")
  expect_equal(expected, class(f))

  mclr <- MultiResFile(mcool_file)
  sclr <- SingleCellFile(scool_file)

  f <- hictkR_open(mclr, resolution = 100000)
  expect_equal(expected, class(f))

  f <- hictkR_open(sclr, cell = "GSM2687248_41669_ACAGTG-R1-DpnII.100000.cool")
  expect_equal(expected, class(f))
})


test_that("hicrkR_open: .mcool", {
  expected <- class(MultiResFile(mcool_file))

  f <- hictkR_open(mcool_file)
  expect_equal(expected, class(f))
})


test_that("hicrkR_open: .scool", {
  expected <- class(SingleCellFile(scool_file))

  f <- hictkR_open(scool_file)
  expect_equal(expected, class(f))
})
