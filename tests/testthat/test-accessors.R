# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

test_that("HiCFile: path accessor", {
  path <- test_path("..", "data", "hic_test_file.hic")
  f <- File(path, 100000)
  expect_equal(f$path, path)
})

test_that("HiCFile: nbins accessor", {
  path <- test_path("..", "data", "hic_test_file.hic")
  f <- File(path, 100000)
  expect_equal(f$nbins, 1380)
})

test_that("HiCFile: file type accessor", {
  path <- test_path("..", "data", "hic_test_file.hic")
  f <- File(path, 100000)
  expect_equal(f$is_hic, TRUE)
  expect_equal(f$is_cooler, FALSE)
})

test_that("HiCFile: file attribute accessor", {
  path1 <- test_path("..", "data", "hic_test_file.hic")
  path2 <- test_path("..", "data", "cooler_test_file.mcool")

  f1 <- File(path1, 100000)
  f2 <- File(path2, 100000)

  expect_equal(f1$attributes$format, "HIC")
  expect_equal(f2$attributes$format, "HDF5::Cooler")
})


test_that("HiCFile: chromosomes accessor", {
  path1 <- test_path("..", "data", "cooler_test_file.mcool")
  path2 <- test_path("..", "data", "chromosomes.tsv.gz")

  chroms <- chromosomes(File(path1, 100000))
  expected_chroms <- read.csv(path2, sep="\t")
  expect_equal(chroms, expected_chroms)
})

test_that("HiCFile: bins accessor", {
  path1 <- test_path("..", "data", "cooler_test_file.mcool")
  path2 <- test_path("..", "data", "hic_test_file.hic")
  path3 <- test_path("..", "data", "bins.tsv.gz")

  bins1 <- bins(File(path1, 100000))
  bins2 <- bins(File(path2, 100000))
  expected_bins <- read.csv(path3, sep="\t", stringsAsFactors=FALSE)

  bins1$chrom <- as.character(bins1$chrom)
  bins2$chrom <- as.character(bins2$chrom)

  expect_equal(bins1, expected_bins)
  expect_equal(bins2, expected_bins)
})

test_that("HiCFile: file normalization accessor", {
  path <- test_path("..", "data", "hic_test_file.hic")
  f <- File(path, 100000)

  expect_equal(f$normalizations, c("ICE"))
})
