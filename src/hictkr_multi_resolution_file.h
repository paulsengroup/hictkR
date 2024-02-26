// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <Rcpp.h>

#include <cstdint>
#include <hictk/multires_file.hpp>
#include <string>

class MultiResFile {
  hictk::MultiResFile _fp;

 public:
  explicit MultiResFile(std::string path);

  [[nodiscard]] std::string path() const;
  [[nodiscard]] Rcpp::DataFrame chromosomes() const;
  [[nodiscard]] Rcpp::IntegerVector resolutions() const;
};
