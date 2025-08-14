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
  test_that("HiCFile: fetch (DF) genome-wide", {
    f <- File(path, 100000)

    df <- fetch(f)
    sum_ <- sum(df$count)
    nnz_ <- length(df$count)

    expect_equal(sum_, 119208613)
    expect_equal(nnz_, 890384)
  })

  test_that("HiCFile: fetch (DF) cis COO", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R:10,000,000-15,000,000")
    sum_ <- sum(df$count)
    num_columns <- length(df)

    expect_equal(sum_, 4519080)
    expect_equal(num_columns, 3)
  })

  test_that("HiCFile: fetch (DF) cis bg2", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R:10,000,000-15,000,000", join = TRUE)
    sum_ <- sum(df$count)
    num_columns <- length(df)

    expect_equal(sum_, 4519080)
    expect_equal(num_columns, 7)
  })

  test_that("HiCFile: fetch (DF) cis BED queries", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R\t10000000\t15000000", query_type = "BED")
    nnz <- length(df$count)

    expect_equal(nnz, 1275)
  })

  test_that("HiCFile: fetch (DF) trans COO", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R:10,000,000-15,000,000", "chrX:0-10,000,000")
    sum_ <- sum(df$count)
    num_columns <- length(df)

    expect_equal(sum_, 83604)
    expect_equal(num_columns, 3)
  })

  test_that("HiCFile: fetch (DF) trans bg2", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R:10,000,000-15,000,000", "chrX:0-10,000,000", join = TRUE)
    sum_ <- sum(df$count)
    num_columns <- length(df)

    expect_equal(sum_, 83604)
    expect_equal(num_columns, 7)
  })

  test_that("HiCFile: fetch (DF) cis: BED queries", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R\t10000000\t15000000", "chrX\t0\t10000000", query_type = "BED")
    nnz <- length(df$count)

    expect_equal(nnz, 4995)
  })

  test_that("HiCFile: fetch (DF) balanced", {
    f <- File(path, 100000)

    if (f$is_cooler) {
      df <- fetch(f, "chr2R:10,000,000-15,000,000", normalization = "weight")
    } else {
      df <- fetch(f, "chr2R:10,000,000-15,000,000", normalization = "ICE")
    }

    sum_ <- sum(df$count)

    expect_equal(sum_, 59.349524704033215)
  })

  test_that("HiCFile: fetch (DF) count_type = int", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", count_type = "int")

    expect_type(m$count, "integer")
  })

  test_that("HiCFile: fetch (DF) count_type = float", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", count_type = "float")

    expect_type(m$count, "double")
  })

  test_that("HiCFile: fetch (DF) count_type = invalid", {
    f <- File(path, 100000)

    expect_error(fetch(f, type = "dense", count_type = "invalid"), regexp = "count_type should be")
  })
}
