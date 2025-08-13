<!--
Copyright (C) 2025 Roberto Rossini <roberros@uio.no>

SPDX-License-Identifier: MIT
-->

# README

The header files found in this folder come from the RcppEigen package.

Source files where extracted from the `RcppEigen_0.3.4.0.2.tar.gz` archive downloaded from CRAN
([link](https://cran.r-project.org/src/contrib/RcppEigen_0.3.4.0.2.tar.gz)). <!-- markdownlint-disable-line MD059 -->
The files were originally located under `inst/include/`.

The original header files required some patching to build using the toolchain provided by `Rtools4*`.

In brief:

- Remove `RcppEigenForward.h` and move relevant `#include` statements in `RcppEigenWrap.h`.
- Fix `#include` statements
- Comment out unnecessary (and problematic) `Rcpp::Exporter`s.
