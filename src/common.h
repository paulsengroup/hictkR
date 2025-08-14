// Copyright (C) 2025 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: GPL-2.0-or-later
//
// This library is free software: you can redistribute it and/or
// modify it under the terms of the GNU Public License as published
// by the Free Software Foundation; either version 3 of the License,
// or (at your option) any later version.
//
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Library General Public License for more details.
//
// You should have received a copy of the GNU Public License along
// with this library.  If not, see
// <https://www.gnu.org/licenses/>.

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
