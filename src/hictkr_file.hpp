// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <Rcpp.h>

#include <cstdint>
#include <hictk/cooler/cooler.hpp>
#include <hictk/file.hpp>
#include <hictk/hic.hpp>
#include <string>

class HiCFile {
  hictk::File _fp;

 public:
  HiCFile() = delete;
  HiCFile(std::string uri, std::uint32_t resolution, std::string matrix_type = "observed",
          std::string matrix_unit = "BP");

  explicit HiCFile(hictk::cooler::File&& clr);
  explicit HiCFile(hictk::hic::File&& hf);

  [[nodiscard]] bool is_cooler() const noexcept;
  [[nodiscard]] bool is_hic() const noexcept;

  [[nodiscard]] Rcpp::DataFrame chromosomes() const;
  [[nodiscard]] Rcpp::DataFrame bins() const;

  [[nodiscard]] std::string path() const noexcept;
  [[nodiscard]] std::uint32_t bin_size() const noexcept;
  [[nodiscard]] std::uint64_t nbins() const noexcept;
  [[nodiscard]] std::uint64_t nchroms() const noexcept;
  [[nodiscard]] Rcpp::List attributes() const;

  [[nodiscard]] Rcpp::DataFrame fetch_df(std::string range1, std::string range2,
                                         std::string normalization, std::string count_type,
                                         bool join, std::string query_type) const;

  [[nodiscard]] Rcpp::NumericMatrix fetch_dense(std::string range1, std::string range2,
                                                std::string normalization, std::string count_type,
                                                std::string query_type) const;

  [[nodiscard]] Rcpp::CharacterVector avail_normalizations() const;
};
