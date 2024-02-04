# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT


mcool_file <- test_path("..", "data", "cooler_test_file.mcool")

test_that("MultiResolutionFile: path accessor", {
  f <- MultiResolutionFile(mcool_file)
  expect_equal(f$path, mcool_file)
})

test_that("MultiResolutionFile: file attribute accessor", {
  f <- MultiResolutionFile(mcool_file)
  expect_equal(f$attributes$format, "HDF5::MCOOL")
})

test_that("MultiResolutionFile: chromosomes accessor", {
  path1 <- mcool_file
  path2 <- test_path("..", "data", "chromosomes.tsv.gz")

  chroms <- MultiResolutionFile(path1)$chromosomes
  expected_chroms <- read.csv(path2, sep="\t")
  expect_equal(chroms, expected_chroms)
})

test_that("MultiResolutionFile: file resolutions accessor", {
  f <- MultiResolutionFile(mcool_file)
  expect_equal(f$resolutions, c(100000, 1000000))
})
