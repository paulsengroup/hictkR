// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include "./hictkr_multi_resolution_file.h"

#include <string>

#include "./common.h"

MultiResFile::MultiResFile(std::string path) : _fp(std::move(path)) {}

std::string MultiResFile::path() const { return _fp.path(); }

Rcpp::DataFrame MultiResFile::chromosomes() const { return get_chromosomes(_fp); }

Rcpp::IntegerVector MultiResFile::resolutions() const {
  return {_fp.resolutions().begin(), _fp.resolutions().end()};
}
