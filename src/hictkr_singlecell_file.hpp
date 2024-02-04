// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <Rcpp.h>

#include <cstdint>
#include <hictk/cooler/singlecell_cooler.hpp>
#include <string>

class SingleCellFile {
  hictk::cooler::SingleCellFile _fp;

 public:
  explicit SingleCellFile(std::string path);

  [[nodiscard]] std::string path() const;
  [[nodiscard]] std::uint32_t bin_size() const noexcept;
  [[nodiscard]] std::uint64_t nbins() const noexcept;
  [[nodiscard]] Rcpp::DataFrame chromosomes() const;
  [[nodiscard]] Rcpp::DataFrame bins() const;
  [[nodiscard]] Rcpp::List attributes() const;
  [[nodiscard]] Rcpp::CharacterVector cells() const;
};
