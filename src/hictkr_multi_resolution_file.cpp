// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include "./hictkr_multi_resolution_file.hpp"

#include <string>

#include "./common.hpp"

MultiResolutionFile::MultiResolutionFile(std::string path) : _fp(std::move(path)) {}

std::string MultiResolutionFile::path() const { return _fp.path(); }

Rcpp::DataFrame MultiResolutionFile::chromosomes() const { return get_chromosomes(_fp); }

Rcpp::List MultiResolutionFile::attributes() const {
  return Rcpp::List::create(Rcpp::Named("format") = _fp.attributes().format,
                            Rcpp::Named("format-version") = _fp.attributes().format_version,
                            Rcpp::Named("bin-type") = _fp.attributes().bin_type.has_value()
                                                          ? *_fp.attributes().bin_type
                                                          : "fixed");
}

Rcpp::IntegerVector MultiResolutionFile::resolutions() const {
  return {_fp.resolutions().begin(), _fp.resolutions().end()};
}
