<!--
Copyright (C) 2025 Roberto Rossini <roberros@uio.no>

SPDX-License-Identifier: GPL-2.0-or-later

This library is free software: you can redistribute it and/or
modify it under the terms of the GNU Public License as published
by the Free Software Foundation; either version 3 of the License,
or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Library General Public License for more details.

You should have received a copy of the GNU Public License along
with this library.  If not, see
<https://www.gnu.org/licenses/>.
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
