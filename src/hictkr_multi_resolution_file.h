// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <Rcpp.h>

#include <cstdint>
#include <hictk/cooler/multires_cooler.hpp>
#include <string>

class MultiResolutionFile {
  hictk::cooler::MultiResFile _fp;

 public:
  explicit MultiResolutionFile(std::string path);

  [[nodiscard]] std::string path() const;
  [[nodiscard]] Rcpp::DataFrame chromosomes() const;
  [[nodiscard]] Rcpp::List attributes() const;
  [[nodiscard]] Rcpp::IntegerVector resolutions() const;
};
