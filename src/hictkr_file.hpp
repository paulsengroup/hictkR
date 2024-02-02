// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <Rcpp.h>
#include <cstdint>
#include <hictk/file.hpp>
#include <hictk/version.hpp>
#include <string>

class HiCFile {
  hictk::File _fp;

public:
  HiCFile() = delete;
  HiCFile(std::string uri, std::uint32_t resolution,
          std::string matrix_type = "observed", std::string matrix_unit = "BP");

  [[nodiscard]] bool is_cooler() const noexcept;
  [[nodiscard]] bool is_hic() const noexcept;

  [[nodiscard]] std::string path() const noexcept;
  [[nodiscard]] std::uint64_t nbins() const noexcept;

  [[nodiscard]] Rcpp::DataFrame fetch_df(std::string range1, std::string range2,
                                         std::string normalization,
                                         std::string count_type, bool join,
                                         std::string query_type);

  [[nodiscard]] Rcpp::NumericMatrix
  fetch_dense(std::string range1, std::string range2, std::string normalization,
              std::string count_type, std::string query_type);
};