# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

test_files <- c(test_path("..", "data", "hic_test_file.hic"),
                test_path("..", "data", "cooler_test_file.mcool"))


for (path in test_files) {
  test_that("HiCFile: fetch (dense) genome-wide", {
    f <- File(path, 100000)

    m <- fetch(f, type="dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(1380, 1380))
    expect_equal(sum_, 178263235)
  })

  test_that("HiCFile: fetch (dense) cis", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", type="dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 50))
    expect_equal(sum_, 6029333)
  })

  test_that("HiCFile: fetch (dense) cis BED queries", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R\t10000000\t15000000", type="dense", query_type="BED")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 50))
    expect_equal(sum_, 6029333)
  })

  test_that("HiCFile: fetch (dense) trans", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R:10,000,000-15,000,000", "chrX:0-10,000,000", type="dense")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 100))
    expect_equal(sum_, 83604)
  })

  test_that("HiCFile: fetch (dense) trans BED queries", {
    f <- File(path, 100000)

    m <- fetch(f, "chr2R\t10000000\t15000000", "chrX\t0\t10000000", type="dense", query_type="BED")

    shape <- dim(m)
    sum_ <- sum(m)

    expect_equal(shape, c(50, 100))
    expect_equal(sum_, 83604)
  })
}
