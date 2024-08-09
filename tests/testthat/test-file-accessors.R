# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT


hic_file <- test_path("..", "data", "hic_test_file.hic")
mcool_file <- test_path("..", "data", "cooler_test_file.mcool")
scool_file <- test_path("..", "data", "cooler_test_file.scool")

test_that("File: path accessor", {
  f <- File(hic_file, 100000)
  expect_equal(f$path, hic_file)
})

test_that("File: nbins accessor", {
  f <- File(hic_file, 100000)
  expect_equal(f$nbins, 1380)
})

test_that("File: file type accessor", {
  f <- File(hic_file, 100000)
  expect_equal(f$is_hic, TRUE)
  expect_equal(f$is_cooler, FALSE)
})

test_that("File: file attribute accessor", {
  f1 <- File(hic_file, 100000)
  f2 <- File(mcool_file, 100000)

  expect_equal(f1$attributes$format, "HIC")
  expect_equal(f2$attributes$format, "HDF5::Cooler")
})


test_that("File: chromosomes accessor", {
  path1 <- mcool_file
  path2 <- test_path("..", "data", "chromosomes.tsv.gz")

  chroms <- File(path1, 100000)$chromosomes
  expected_chroms <- read.csv(path2, sep = "\t")
  expect_equal(chroms, expected_chroms)
})

test_that("File: bins accessor", {
  path1 <- mcool_file
  path2 <- hic_file
  path3 <- test_path("..", "data", "bins.tsv.gz")

  bins1 <- File(path1, 100000)$bins
  bins2 <- File(path2, 100000)$bins
  expected_bins <- read.csv(path3, sep = "\t", stringsAsFactors = FALSE)

  bins1$chrom <- as.character(bins1$chrom)
  bins2$chrom <- as.character(bins2$chrom)

  expect_equal(bins1, expected_bins)
  expect_equal(bins2, expected_bins)
})

test_that("File: file normalization accessor", {
  f <- File(hic_file, 100000)

  expect_equal(f$normalizations, c("ICE"))
})
