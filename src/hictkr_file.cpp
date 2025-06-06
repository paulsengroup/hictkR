// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include "./hictkr_file.h"

#include <Rcpp.h>
#include <fmt/format.h>

#include <cstddef>
#include <cstdint>
#include <hictk/bin_table.hpp>
#include <hictk/file.hpp>
#include <hictk/genomic_interval.hpp>
#include <hictk/pixel.hpp>
#include <hictk/transformers/join_genomic_coords.hpp>
#include <limits>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <variant>
#include <vector>

#include "./common.h"

[[nodiscard]] static std::optional<std::uint32_t> get_resolution_checked(
    std::optional<std::int64_t> resolution) {
  if (!resolution.has_value()) {
    return {};
  }

  if (*resolution < 0) {
    throw std::invalid_argument("resolution cannot be negative");
  }

  constexpr auto max_res = std::numeric_limits<std::uint32_t>::max();
  if (*resolution > max_res) {
    throw std::invalid_argument(
        fmt::format(FMT_STRING("resolution cannot be greater than {}"), max_res));
  }

  return static_cast<std::uint32_t>(*resolution);
}

HiCFile::HiCFile(std::string uri, std::optional<std::int64_t> resolution_, std::string matrix_type,
                 std::string matrix_unit)
    : _fp(uri, get_resolution_checked(resolution_), hictk::hic::ParseMatrixTypeStr(matrix_type),
          hictk::hic::ParseUnitStr(matrix_unit)) {}

HiCFile::HiCFile(std::string uri, std::string matrix_type, std::string matrix_unit)
    : HiCFile(std::move(uri), std::nullopt, std::move(matrix_type), std::move(matrix_unit)) {}

HiCFile::HiCFile(std::string uri, std::int64_t resolution_, std::string matrix_type,
                 std::string matrix_unit)
    : HiCFile(std::move(uri), std::make_optional(resolution_), std::move(matrix_type),
              std::move(matrix_unit)) {}

HiCFile::HiCFile(hictk::cooler::File &&clr) : _fp(std::move(clr)) {}
HiCFile::HiCFile(hictk::hic::File &&hf) : _fp(std::move(hf)) {}

bool HiCFile::is_cooler() const noexcept { return _fp.is_cooler(); }
bool HiCFile::is_hic() const noexcept { return _fp.is_hic(); }

Rcpp::DataFrame HiCFile::chromosomes() const { return get_chromosomes(_fp); }

Rcpp::DataFrame HiCFile::bins() const { return get_bins(_fp); }

std::string HiCFile::path() const noexcept { return {_fp.path()}; }
std::uint32_t HiCFile::resolution() const noexcept { return _fp.resolution(); }
std::uint64_t HiCFile::nbins() const noexcept { return _fp.nbins(); }
std::uint64_t HiCFile::nchroms() const noexcept { return _fp.nchroms(); }

[[nodiscard]] static Rcpp::List get_cooler_attrs(const hictk::cooler::File &clr) {
  Rcpp::List r_attrs{};
  std::vector<std::string> r_attr_names{};

  const auto &attrs = clr.attributes();

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
  if (attrs.nnz.has_value()) {
    r_attr_names.push_back("nnz");
    r_attrs.push_back(*attrs.nnz);
  }
  if (attrs.sum.has_value()) {
    r_attr_names.push_back("sum");
    std::visit([&](const auto &sum) { r_attrs.push_back(sum); }, *attrs.sum);
  }
  if (attrs.cis.has_value()) {
    r_attr_names.push_back("cis");
    std::visit([&](const auto &cis) { r_attrs.push_back(cis); }, *attrs.cis);
  }

  r_attrs.attr("names") = r_attr_names;

  return r_attrs;
}

[[nodiscard]] static Rcpp::List get_hic_attrs(const hictk::hic::File &hf) {
  // clang-format off
  return Rcpp::List::create(
            Rcpp::Named("bin-size") = hf.resolution(),
            Rcpp::Named("format") = "HIC",
            Rcpp::Named("format-version") = hf.version(),
            Rcpp::Named("assembly") = hf.assembly(),
            Rcpp::Named("format-url") = "https://github.com/aidenlab/hic-format",
            Rcpp::Named("nbins") = hf.nbins(),
            Rcpp::Named("nchroms") = hf.nchroms()
         );
  // clang-format on
}

Rcpp::List HiCFile::attributes() const {
  Rcpp::List attrs{};

  std::vector<std::string> attr_names;
  if (is_cooler()) {
    return get_cooler_attrs(_fp.get<hictk::cooler::File>());
  }
  return get_hic_attrs(_fp.get<hictk::hic::File>());
}

template <typename N, typename Selector>
static Rcpp::DataFrame fetch_as_df(const Selector &sel,
                                   const std::shared_ptr<const hictk::BinTable> &bins_ptr,
                                   bool join) {
  if (!join) {
    std::vector<int64_t> bin1_ids{};
    std::vector<int64_t> bin2_ids{};
    std::vector<N> counts{};

    std::for_each(sel.template begin<N>(), sel.template end<N>(),
                  [&](const hictk::ThinPixel<N> &p) {
                    bin1_ids.push_back(p.bin1_id);
                    bin2_ids.push_back(p.bin2_id);
                    counts.push_back(p.count);
                  });

    return Rcpp::DataFrame::create(Rcpp::Named("bin1_id") = bin1_ids,
                                   Rcpp::Named("bin2_id") = bin2_ids,
                                   Rcpp::Named("count") = counts);
  }

  Rcpp::CharacterVector chrom_names{};
  for (const auto &chrom : bins_ptr->chromosomes()) {
    chrom_names.push_back(std::string{chrom.name()});
  }

  std::vector<std::int32_t> chrom1_ids{};
  std::vector<std::int32_t> start1{};
  std::vector<std::int32_t> end1{};
  std::vector<std::int32_t> chrom2_ids{};
  std::vector<std::int32_t> start2{};
  std::vector<std::int32_t> end2{};
  std::vector<N> counts{};

  const hictk::transformers::JoinGenomicCoords jsel(sel.template begin<N>(), sel.template end<N>(),
                                                    bins_ptr);

  std::for_each(jsel.begin(), jsel.end(), [&](const hictk::Pixel<N> &p) {
    chrom1_ids.push_back(p.coords.bin1.chrom().id() + 1);
    start1.push_back(p.coords.bin1.start());
    end1.push_back(p.coords.bin1.end());
    chrom2_ids.push_back(p.coords.bin2.chrom().id() + 1);
    start2.push_back(p.coords.bin2.start());
    end2.push_back(p.coords.bin2.end());
    counts.push_back(p.count);
  });

  Rcpp::IntegerVector chrom1{chrom1_ids.begin(), chrom1_ids.end()};
  Rcpp::IntegerVector chrom2{chrom2_ids.begin(), chrom2_ids.end()};

  chrom1.attr("class") = "factor";
  chrom1.attr("levels") = chrom_names;
  chrom2.attr("class") = "factor";
  chrom2.attr("levels") = chrom_names;

  return Rcpp::DataFrame::create(Rcpp::Named("chrom1") = chrom1, Rcpp::Named("start1") = start1,
                                 Rcpp::Named("end1") = end1, Rcpp::Named("chrom2") = chrom2,
                                 Rcpp::Named("start2") = start2, Rcpp::Named("end2") = end2,
                                 Rcpp::Named("count") = counts);
}

Rcpp::DataFrame HiCFile::fetch_df(std::string range1, std::string range2, std::string normalization,
                                  std::string count_type, bool join, std::string query_type) const {
  if (normalization != "NONE") {
    count_type = "float";
  }

  if (range1.empty()) {
    assert(range2.empty());
    return std::visit(
        [&](const auto &ff) {
          auto sel = ff.fetch(hictk::balancing::Method{normalization});
          if (count_type == "int") {
            return fetch_as_df<std::int32_t>(sel, ff.bins_ptr(), join);
          }
          return fetch_as_df<double>(sel, ff.bins_ptr(), join);
        },
        _fp.get());
  }

  const auto qt =
      query_type == "UCSC" ? hictk::GenomicInterval::Type::UCSC : hictk::GenomicInterval::Type::BED;

  return std::visit(
      [&](const auto &ff) {
        auto sel = range2.empty() || range1 == range2
                       ? ff.fetch(range1, hictk::balancing::Method{normalization}, qt)
                       : ff.fetch(range1, range2, hictk::balancing::Method{normalization}, qt);
        if (count_type == "int") {
          return fetch_as_df<std::int32_t>(sel, ff.bins_ptr(), join);
        }
        return fetch_as_df<double>(sel, ff.bins_ptr(), join);
      },
      _fp.get());
}

template <typename N, typename Selector, typename MatrixT>
static void fill_dense_matrix(const Selector &sel, MatrixT &matrix, bool mirror_matrix,
                              std::uint64_t row_offset = 0, std::uint64_t col_offset = 0) {
  const auto num_rows = matrix.nrow();
  const auto num_cols = matrix.ncol();

  std::for_each(sel.template begin<N>(), sel.template end<N>(), [&](const auto &tp) {
    const auto i1 = static_cast<std::int64_t>(tp.bin1_id - row_offset);
    const auto i2 = static_cast<std::int64_t>(tp.bin2_id - col_offset);
    matrix.at(i1, i2) = tp.count;

    if (mirror_matrix) {
      const auto delta = i2 - i1;
      if (delta >= 0 && delta < num_rows && i1 < num_cols && i2 < num_rows) {
        matrix.at(i2, i1) = tp.count;
      } else if ((delta < 0 || delta > num_cols) && i1 < num_cols && i2 < num_rows) {
        const auto i3 = static_cast<std::int64_t>(tp.bin2_id - row_offset);
        const auto i4 = static_cast<std::int64_t>(tp.bin1_id - col_offset);

        if (i3 >= 0 && i3 < num_rows && i4 >= 0 && i4 < num_cols) {
          matrix.at(i3, i4) = tp.count;
        }
      }
    }
  });
}

template <typename N, typename Selector,
          typename RcppMatrixT =
              std::conditional_t<std::is_integral_v<N>, Rcpp::IntegerMatrix, Rcpp::NumericMatrix>>
static RcppMatrixT fetch_as_matrix(const Selector &sel) {
  const auto bin_size = sel.bins().resolution();

  const auto span1 = sel.coord1().bin2.end() - sel.coord1().bin1.start();
  const auto span2 = sel.coord2().bin2.end() - sel.coord2().bin1.start();
  const auto num_rows =
      static_cast<std::int64_t>(span1 == 0 ? sel.bins().size() : (span1 + bin_size - 1) / bin_size);
  const auto num_cols =
      static_cast<std::int64_t>(span2 == 0 ? sel.bins().size() : (span2 + bin_size - 1) / bin_size);

  constexpr auto bad_bin_id = std::numeric_limits<std::uint64_t>::max();

  const auto row_offset =
      static_cast<std::int64_t>(sel.coord1().bin1.id() == bad_bin_id ? 0 : sel.coord1().bin1.id());
  const auto col_offset =
      static_cast<std::int64_t>(sel.coord2().bin1.id() == bad_bin_id ? 0 : sel.coord2().bin1.id());

  const auto mirror_matrix = sel.coord1().bin1.chrom() == sel.coord2().bin1.chrom();

  // Matrix allocated this way is zero-filled
  RcppMatrixT matrix(num_rows, num_cols);
  fill_dense_matrix<N>(sel, matrix, mirror_matrix, row_offset, col_offset);
  return matrix;
}

template <typename N, typename RcppMatrixT = std::conditional_t<
                          std::is_integral_v<N>, Rcpp::IntegerMatrix, Rcpp::NumericMatrix>>
static RcppMatrixT fetch_as_matrix(const hictk::hic::PixelSelectorAll &sel) {
  const auto num_rows = static_cast<std::int64_t>(sel.bins().size());
  const auto num_cols = static_cast<std::int64_t>(sel.bins().size());

  // Matrix allocated this way is zero-filled
  RcppMatrixT matrix(num_rows, num_cols);
  fill_dense_matrix<N>(sel, matrix, true);
  return matrix;
}

Rcpp::RObject HiCFile::fetch_dense(std::string range1, std::string range2,
                                   std::string normalization, std::string count_type,
                                   std::string query_type) const {
  if (normalization != "NONE") {
    count_type = "float";
  }

  if (range1.empty()) {
    assert(range2.empty());
    return std::visit(
        [&](const auto &ff) {
          auto sel = ff.fetch(hictk::balancing::Method{normalization});
          if (count_type == "int") {
            return static_cast<Rcpp::RObject>(fetch_as_matrix<std::int32_t>(sel));
          }
          return static_cast<Rcpp::RObject>(fetch_as_matrix<double>(sel));
        },
        _fp.get());
  }

  const auto qt =
      query_type == "UCSC" ? hictk::GenomicInterval::Type::UCSC : hictk::GenomicInterval::Type::BED;

  return std::visit(
      [&](const auto &ff) {
        auto sel = range2.empty() || range1 == range2
                       ? ff.fetch(range1, hictk::balancing::Method{normalization}, qt)
                       : ff.fetch(range1, range2, hictk::balancing::Method{normalization}, qt);
        if (count_type == "int") {
          return static_cast<Rcpp::RObject>(fetch_as_matrix<std::int32_t>(sel));
        }
        return static_cast<Rcpp::RObject>(fetch_as_matrix<double>(sel));
      },
      _fp.get());
}

Rcpp::CharacterVector HiCFile::avail_normalizations() const {
  Rcpp::CharacterVector norms{};
  for (const auto &norm : _fp.avail_normalizations()) {
    norms.push_back(norm.to_string());
  }
  return norms;
}
