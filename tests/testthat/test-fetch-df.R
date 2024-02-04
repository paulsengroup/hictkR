# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

test_files <- c(test_path("..", "data", "hic_test_file.hic"),
                test_path("..", "data", "cooler_test_file.mcool"))

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

    df <- fetch(f, "chr2R:10,000,000-15,000,000", join=TRUE)
    sum_ <- sum(df$count)
    num_columns <- length(df)

    expect_equal(sum_, 4519080)
    expect_equal(num_columns, 7)
  })

  test_that("HiCFile: fetch (DF) cis BED queries", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R\t10000000\t15000000", query_type="BED")
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

    df <- fetch(f, "chr2R:10,000,000-15,000,000", "chrX:0-10,000,000", join=TRUE)
    sum_ <- sum(df$count)
    num_columns <- length(df)

    expect_equal(sum_, 83604)
    expect_equal(num_columns, 7)
  })

  test_that("HiCFile: fetch (DF) cis: BED queries", {
    f <- File(path, 100000)

    df <- fetch(f, "chr2R\t10000000\t15000000", "chrX\t0\t10000000", query_type="BED")
    nnz <- length(df$count)

    expect_equal(nnz, 4995)
  })

  test_that("HiCFile: fetch (DF) balanced", {
    f <- File(path, 100000)

    if (f$is_cooler) {
      df <- fetch(f, "chr2R:10,000,000-15,000,000", normalization="weight")
    } else {
      df <- fetch(f, "chr2R:10,000,000-15,000,000", normalization="ICE")
    }

    sum_ <- sum(df$count)

    expect_equal(sum_, 59.349524704033215)
  })

}
