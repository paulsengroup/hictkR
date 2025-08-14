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


test_files <- c(
  test_path("..", "data", "hic_test_file.hic"),
  test_path("..", "data", "cooler_test_file.mcool")
)


for (path in test_files) {
  test_that("HiCFile: fetch (dense) genome-wide", {
    f <- File(path, 100000)

    m <- fetch(f, type = "dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(1380, 1380))
    expect_equal(sum_, 178263235)
    expect_equal(m, t(m))
  })

  test_that("HiCFile: fetch (dense) symmetric cis", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", type = "dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 50))
    expect_equal(sum_, 6029333)
    expect_equal(m, t(m))
  })

  test_that("HiCFile: fetch (dense) asymmetric cis", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2L:0-10,000,000", "chr2L:5,000,000-20,000,000", type = "dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(100, 150))
    expect_equal(sum_, 6287451)


    m <- fetch(f, "chr2L:0-10,000,000", "chr2L:10,000,000-20,000,000", type = "dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(100, 100))
    expect_equal(sum_, 761223)

    m <- fetch(f, "chr2L:0-10,000,000", "chr2L:0-15,000,000", type = "dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(100, 150))
    expect_equal(sum_, 12607205)
  })

  test_that("HiCFile: fetch (dense) cis BED queries", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R\t10000000\t15000000", type = "dense", query_type = "BED")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 50))
    expect_equal(sum_, 6029333)
  })

  test_that("HiCFile: fetch (dense) trans", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", "chrX:0-10,000,000", type = "dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 100))
    expect_equal(sum_, 83604)
  })

  test_that("HiCFile: fetch (dense) trans BED queries", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R\t10000000\t15000000", "chrX\t0\t10000000", type = "dense", query_type = "BED")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 100))
    expect_equal(sum_, 83604)
  })

  test_that("HiCFile: fetch (dense) count_type = int", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", type = "dense", count_type = "int")

    expect_type(m, "integer")
  })

  test_that("HiCFile: fetch (dense) count_type = float", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", type = "dense", count_type = "float")

    expect_type(m, "double")
  })

  test_that("HiCFile: fetch (dense) count_type = invalid", {
    f <- File(path, 100000)

    expect_error(fetch(f, type = "dense", count_type = "invalid"), regexp = "count_type should be")
  })
}
