// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include "./hictkr_singlecell_file.h"

#include <cstdint>
#include <hictk/cooler/singlecell_cooler.hpp>
#include <string>
#include <vector>

#include "./common.h"

SingleCellFile::SingleCellFile(std::string path) : _fp(std::move(path)) {}

std::string SingleCellFile::path() const { return _fp.path(); }

std::uint32_t SingleCellFile::resolution() const noexcept { return _fp.resolution(); }

std::uint64_t SingleCellFile::nbins() const noexcept { return _fp.bins().size(); }

Rcpp::DataFrame SingleCellFile::chromosomes() const { return get_chromosomes(_fp); }

Rcpp::DataFrame SingleCellFile::bins() const { return get_bins(_fp); }

Rcpp::List SingleCellFile::attributes() const {
  Rcpp::List r_attrs{};
  std::vector<std::string> r_attr_names{};

  const auto &attrs = _fp.attributes();

  r_attr_names.push_back("bin-size");
  r_attrs.push_back(attrs.bin_size);

  r_attr_names.push_back("bin-type");
  switch (attrs.bin_type) {
    case hictk::BinTable::Type::fixed: {
      r_attrs.push_back("fixed");
      break;
    }
    case hictk::BinTable::Type::variable: {
      r_attrs.push_back("variable");
      break;
    }
  }

  r_attr_names.push_back("format");
  r_attrs.push_back(attrs.format);

  r_attr_names.push_back("format-version");
  r_attrs.push_back(attrs.format_version);

  if (attrs.storage_mode.has_value()) {
    r_attr_names.push_back("storage-mode");
    r_attrs.push_back(*attrs.storage_mode);
  }
  if (attrs.creation_date.has_value()) {
    r_attr_names.push_back("creation-date");
    r_attrs.push_back(*attrs.creation_date);
  }
  if (attrs.generated_by.has_value()) {
    r_attr_names.push_back("generated-by");
    r_attrs.push_back(*attrs.generated_by);
  }
  if (attrs.assembly.has_value()) {
    r_attr_names.push_back("assembly");
    r_attrs.push_back(*attrs.assembly);
  }
  if (attrs.metadata.has_value()) {
    r_attr_names.push_back("metadata");
    r_attrs.push_back(*attrs.metadata);
  }
  if (attrs.format_url.has_value()) {
    r_attr_names.push_back("format-url");
    r_attrs.push_back(*attrs.format_url);
  }
  if (attrs.nbins.has_value()) {
    r_attr_names.push_back("nbins");
    r_attrs.push_back(*attrs.nbins);
  }
  if (attrs.nchroms.has_value()) {
    r_attr_names.push_back("nchroms");
    r_attrs.push_back(*attrs.nchroms);
  }
  if (attrs.ncells.has_value()) {
    r_attr_names.push_back("ncells");
    r_attrs.push_back(*attrs.ncells);
  }

  r_attrs.attr("names") = r_attr_names;

  return r_attrs;
}

Rcpp::CharacterVector SingleCellFile::cells() const {
  return {_fp.cells().begin(), _fp.cells().end()};
}
