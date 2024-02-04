// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include <Rcpp.h>

#include "./hictkr_file.hpp"

RCPP_MODULE(hictkR) {
  Rcpp::class_<HiCFile>("HiCFile")
      .constructor<std::string, std::uint32_t, std::string, std::string>()
      .property("is_cooler", &HiCFile::is_cooler)
      .property("is_hic", &HiCFile::is_hic)
      .property("chromosomes", &HiCFile::chromosomes)
      .property("bins", &HiCFile::bins)
      .property("path", &HiCFile::path, "Path to the opened file.")
      .property("nbins", &HiCFile::nbins, "Number of bins.")
      .property("nchroms", &HiCFile::nchroms, "Number of chromosomes.")
      .property("attributes", &HiCFile::attributes, "File attributes.")
      .property("normalizations", &HiCFile::avail_normalizations, "Normalizations available.")
      .method("fetch_df", &HiCFile::fetch_df, "Fetch interactions as a DataFrame.")
      .method("fetch_dense", &HiCFile::fetch_dense, "Fetch interactions as a Matrix.");
}
