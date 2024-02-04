// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include <Rcpp.h>

#include <cstdint>
#include <string>

#include "./hictkr_file.hpp"
#include "./hictkr_multi_resolution_file.hpp"
#include "./hictkr_singlecell_file.hpp"
#include "./hictkr_validation.hpp"

RCPP_MODULE(hictkR) {
  Rcpp::function("is_cooler", &is_cooler, "Test whether a file or URI is a Cooler.");
  Rcpp::function("is_multires_file", &is_multires_file,
                 "Test whether a file is a multi-resolution Cooler.");
  Rcpp::function("is_scool_file", &is_scool_file, "Test whether a file is a single-cell Cooler.");
  Rcpp::function("is_hic_file", &is_hic_file, "Test whether a file is in .hic format.");

  Rcpp::class_<HiCFile>("RcppHiCFile")
      .constructor<std::string, std::uint32_t, std::string, std::string>()
      .property("is_cooler", &HiCFile::is_cooler)
      .property("is_hic", &HiCFile::is_hic)
      .property("chromosomes", &HiCFile::chromosomes)
      .property("bins", &HiCFile::bins)
      .property("path", &HiCFile::path, "Path to the opened file.")
      .property("bin_size", &HiCFile::bin_size, "File bin size in bp.")
      .property("nbins", &HiCFile::nbins, "Number of bins.")
      .property("nchroms", &HiCFile::nchroms, "Number of chromosomes.")
      .property("attributes", &HiCFile::attributes, "File attributes.")
      .property("normalizations", &HiCFile::avail_normalizations, "Normalizations available.")
      .const_method("fetch_df", &HiCFile::fetch_df, "Fetch interactions as a DataFrame.")
      .const_method("fetch_dense", &HiCFile::fetch_dense, "Fetch interactions as a Matrix.");

  Rcpp::class_<MultiResolutionFile>("RcppMultiResolutionFile")
      .constructor<std::string>()
      .property("path", &MultiResolutionFile::path, "Path to the opened file.")
      .property("chromosomes", &MultiResolutionFile::chromosomes)
      .property("attributes", &MultiResolutionFile::attributes, "File attributes.")
      .property("resolutions", &MultiResolutionFile::resolutions);

  Rcpp::class_<SingleCellFile>("RcppSingleCellFile")
      .constructor<std::string>()
      .property("path", &SingleCellFile::path, "Path to the opened file.")
      .property("bin_size", &SingleCellFile::bin_size)
      .property("nbins", &SingleCellFile::nbins)
      .property("chromosomes", &SingleCellFile::chromosomes)
      .property("bins", &SingleCellFile::bins)
      .property("attributes", &SingleCellFile::attributes, "File attributes.")
      .property("cells", &SingleCellFile::cells);
}
