// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <Rcpp.h>

#include <cstdint>
#include <vector>

template <typename File>
[[nodiscard]] Rcpp::DataFrame get_chromosomes(const File& f) {
  std::vector<std::string> chrom_names{};
  std::vector<std::uint32_t> chrom_sizes{};
  for (const auto& chrom : f.chromosomes()) {
    if (chrom.is_all()) {
      continue;
    }
    chrom_names.push_back(std::string{chrom.name()});
    chrom_sizes.push_back(chrom.size());
  }

  return Rcpp::DataFrame::create(Rcpp::Named("name") = chrom_names,
                                 Rcpp::Named("size") = chrom_sizes);
}

template <typename File>
[[nodiscard]] Rcpp::DataFrame get_bins(const File& f) {
  Rcpp::CharacterVector chrom_names{};
  for (const auto& chrom : f.chromosomes()) {
    chrom_names.push_back(std::string{chrom.name()});
  }

  std::vector<std::uint32_t> chrom_ids{};
  std::vector<std::uint32_t> starts{};
  std::vector<std::uint32_t> ends{};

  for (const auto& bin : f.bins()) {
    chrom_ids.push_back(bin.chrom().id() + 1);
    starts.push_back(bin.start());
    ends.push_back(bin.end());
  }

  Rcpp::IntegerVector chroms(chrom_ids.begin(), chrom_ids.end());

  chroms.attr("class") = "factor";
  chroms.attr("levels") = chrom_names;

  return Rcpp::DataFrame::create(Rcpp::Named("chrom") = chroms, Rcpp::Named("start") = starts,
                                 Rcpp::Named("end") = ends);
}
