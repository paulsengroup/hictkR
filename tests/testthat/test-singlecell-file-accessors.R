# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT


scool_file <- test_path("..", "data", "cooler_test_file.scool")

test_that("SingleCellFile: path accessor", {
  f <- SingleCellFile(scool_file)
  expect_equal(f$path, scool_file)
})

test_that("SingleCellFile: file attribute accessor", {
  f <- SingleCellFile(scool_file)
  expect_equal(f$attributes$format, "HDF5::SCOOL")
})

test_that("File: nbins accessor", {
  f <- SingleCellFile(scool_file)
  expect_equal(f$nbins, 26398)
})

test_that("File: bins accessor", {
  bins <- SingleCellFile(scool_file)$bins
  expect_equal(length(bins$chrom), 26398)
})


test_that("SingleCellFile: chromosomes accessor", {
  chroms <- SingleCellFile(scool_file)$chromosomes
  expect_equal(length(chroms$name), 20)
})

test_that("SingleCellFile: file cells accessor", {
  f <- SingleCellFile(scool_file)
  expect_equal(
    f$cells,
    c(
      "GSM2687248_41669_ACAGTG-R1-DpnII.100000.cool",
      "GSM2687249_41670_GGCTAC-R1-DpnII.100000.cool",
      "GSM2687250_41671_TTAGGC-R1-DpnII.100000.cool",
      "GSM2687251_41672_AGTTCC-R1-DpnII.100000.cool",
      "GSM2687252_41673_CCGTCC-R1-DpnII.100000.cool"
    )
  )
})
