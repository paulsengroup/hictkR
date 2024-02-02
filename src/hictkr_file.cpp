// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include <Rcpp.h>
#include <cstddef>
#include <cstdint>
#include <hictk/bin_table.hpp>
#include <hictk/file.hpp>
#include <hictk/genomic_interval.hpp>
#include <hictk/pixel.hpp>
#include <hictk/transformers/join_genomic_coords.hpp>
#include <memory>
#include <string>
#include <variant>
#include <vector>

#include "./hictkr_file.hpp"

HiCFile::HiCFile(std::string uri, std::uint32_t resolution,
                 std::string matrix_type, std::string matrix_unit)
    : _fp(uri, resolution, hictk::hic::ParseMatrixTypeStr(matrix_type),
          hictk::hic::ParseUnitStr(matrix_unit)) {}

bool HiCFile::is_cooler() const noexcept { return _fp.is_cooler(); }
bool HiCFile::is_hic() const noexcept { return _fp.is_hic(); }

Rcpp::DataFrame HiCFile::chromosomes() const {
  Rcpp::CharacterVector chrom_names{};
  Rcpp::IntegerVector chrom_sizes{};
  for (const auto &chrom : _fp.chromosomes()) {
    if (chrom.is_all()) {
      continue;
    }
    chrom_names.push_back(std::string{chrom.name()});
    chrom_sizes.push_back(chrom.size());
  }

  return Rcpp::DataFrame::create(Rcpp::Named("name") = chrom_names,
                                 Rcpp::Named("size") = chrom_sizes);
}

Rcpp::DataFrame HiCFile::bins() const {

  Rcpp::CharacterVector chrom_names{};
  for (const auto &chrom : _fp.chromosomes()) {
    chrom_names.push_back(std::string{chrom.name()});
  }

  Rcpp::IntegerVector chroms{};
  Rcpp::IntegerVector starts{};
  Rcpp::IntegerVector ends{};

  for (const auto &bin : _fp.bins()) {
    chroms.push_back(bin.chrom().id() + 1);
    starts.push_back(bin.start());
    ends.push_back(bin.end());
  }

  chroms.attr("class") = "factor";
  chroms.attr("levels") = chrom_names;

  return Rcpp::DataFrame::create(Rcpp::Named("chrom") = chroms,
                                 Rcpp::Named("start") = starts,
                                 Rcpp::Named("end") = ends);
}

std::string HiCFile::path() const noexcept { return {_fp.path()}; }
std::uint64_t HiCFile::nbins() const noexcept { return _fp.nbins(); }

template <typename N, typename Selector>
static Rcpp::DataFrame
fetch_as_df(const Selector &sel,
            const std::shared_ptr<const hictk::BinTable> &bins_ptr, bool join) {

  Rcpp::NumericVector counts{};

  if (!join) {
    Rcpp::IntegerVector bin1_ids{};
    Rcpp::IntegerVector bin2_ids{};

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

  Rcpp::IntegerVector chrom1{};
  Rcpp::IntegerVector start1{};
  Rcpp::IntegerVector end1{};
  Rcpp::IntegerVector chrom2{};
  Rcpp::IntegerVector start2{};
  Rcpp::IntegerVector end2{};

  const hictk::transformers::JoinGenomicCoords jsel(
      sel.template begin<N>(), sel.template end<N>(), bins_ptr);

  std::for_each(jsel.begin(), jsel.end(), [&](const hictk::Pixel<N> &p) {
    chrom1.push_back(p.coords.bin1.chrom().id() + 1);
    start1.push_back(p.coords.bin1.start());
    end1.push_back(p.coords.bin1.end());
    chrom2.push_back(p.coords.bin2.chrom().id() + 1);
    start2.push_back(p.coords.bin2.start());
    end2.push_back(p.coords.bin2.end());
    counts.push_back(p.count);
  });

  chrom1.attr("class") = "factor";
  chrom1.attr("levels") = chrom_names;
  chrom2.attr("class") = "factor";
  chrom2.attr("levels") = chrom_names;

  return Rcpp::DataFrame::create(
      Rcpp::Named("chrom1") = chrom1, Rcpp::Named("start1") = start1,
      Rcpp::Named("end1") = end1, Rcpp::Named("chrom2") = chrom2,
      Rcpp::Named("start2") = start2, Rcpp::Named("end2") = end2,
      Rcpp::Named("count") = counts);
}

Rcpp::DataFrame HiCFile::fetch_df(std::string range1, std::string range2,
                                  std::string normalization,
                                  std::string count_type, bool join,
                                  std::string query_type) {

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

  const auto qt = query_type == "UCSC" ? hictk::GenomicInterval::Type::UCSC
                                       : hictk::GenomicInterval::Type::BED;

  return std::visit(
      [&](const auto &ff) {
        auto sel =
            range2.empty() || range1 == range2
                ? ff.fetch(range1, hictk::balancing::Method{normalization}, qt)
                : ff.fetch(range1, range2,
                           hictk::balancing::Method{normalization}, qt);
        if (count_type == "int") {
          return fetch_as_df<std::int32_t>(sel, ff.bins_ptr(), join);
        }
        return fetch_as_df<double>(sel, ff.bins_ptr(), join);
      },
      _fp.get());
}

template <typename N, typename Selector>
static Rcpp::NumericMatrix fetch_as_matrix(const Selector &sel,
                                           bool mirror_below_diagonal = true) {

  const auto bin_size = sel.bins().bin_size();

  const auto span1 = sel.coord1().bin2.end() - sel.coord1().bin1.start();
  const auto span2 = sel.coord2().bin2.end() - sel.coord2().bin1.start();
  const auto num_rows =
      span1 == 0 ? sel.bins().size() : (span1 + bin_size - 1) / bin_size;
  const auto num_cols =
      span2 == 0 ? sel.bins().size() : (span2 + bin_size - 1) / bin_size;

  const auto row_offset = sel.coord1().bin1.id();
  const auto col_offset = sel.coord2().bin1.id();

  Rcpp::NumericMatrix matrix(num_rows, num_cols);
  std::fill(matrix.begin(), matrix.end(), N{0});

  std::for_each(
      sel.template begin<N>(), sel.template end<N>(), [&](const auto &tp) {
        const auto i1 = static_cast<std::int64_t>(tp.bin1_id - row_offset);
        const auto i2 = static_cast<std::int64_t>(tp.bin2_id - col_offset);
        matrix.at(i1, i2) = tp.count;

        if (mirror_below_diagonal) {
          //  Mirror matrix below diagonal
          if (i2 - i1 < num_rows && i1 < num_cols && i2 < num_rows) {
            matrix.at(i2, i1) = tp.count;
          } else if (i2 - i1 > num_cols && i1 < num_cols && i2 < num_rows) {
            const auto i3 = static_cast<std::int64_t>(tp.bin2_id - row_offset);
            const auto i4 = static_cast<std::int64_t>(tp.bin1_id - col_offset);
            matrix.at(i3, i4) = tp.count;
          }
        }
      });
  return matrix;
}

template <typename N>
static Rcpp::NumericMatrix
fetch_as_matrix(const hictk::hic::PixelSelectorAll &sel,
                bool mirror_below_diagonal = true) {

  const auto bin_size = sel.bins().bin_size();

  const auto num_rows = sel.bins().size();
  const auto num_cols = sel.bins().size();

  Rcpp::NumericMatrix matrix(num_rows, num_cols);
  std::fill(matrix.begin(), matrix.end(), N{0});

  std::for_each(
      sel.template begin<N>(), sel.template end<N>(), [&](const auto &tp) {
        const auto i1 = static_cast<std::int64_t>(tp.bin1_id);
        const auto i2 = static_cast<std::int64_t>(tp.bin2_id);
        matrix.at(i1, i2) = tp.count;

        if (mirror_below_diagonal) {
          //  Mirror matrix below diagonal
          if (i2 - i1 < num_rows && i1 < num_cols && i2 < num_rows) {
            matrix.at(i2, i1) = tp.count;
          } else if (i2 - i1 > num_cols && i1 < num_cols && i2 < num_rows) {
            const auto i3 = static_cast<std::int64_t>(tp.bin2_id);
            const auto i4 = static_cast<std::int64_t>(tp.bin1_id);
            matrix.at(i3, i4) = tp.count;
          }
        }
      });
  return matrix;
}

Rcpp::NumericMatrix HiCFile::fetch_dense(std::string range1, std::string range2,
                                         std::string normalization,
                                         std::string count_type,
                                         std::string query_type) {
  if (normalization != "NONE") {
    count_type = "float";
  }

  if (range1.empty()) {
    assert(range2.empty());
    return std::visit(
        [&](const auto &ff) {
          auto sel = ff.fetch(hictk::balancing::Method{normalization});
          if (count_type == "int") {
            return fetch_as_matrix<std::int32_t>(sel);
          }
          return fetch_as_matrix<double>(sel);
        },
        _fp.get());
  }

  const auto qt = query_type == "UCSC" ? hictk::GenomicInterval::Type::UCSC
                                       : hictk::GenomicInterval::Type::BED;

  return std::visit(
      [&](const auto &ff) {
        auto sel =
            range2.empty() || range1 == range2
                ? ff.fetch(range1, hictk::balancing::Method{normalization}, qt)
                : ff.fetch(range1, range2,
                           hictk::balancing::Method{normalization}, qt);
        if (count_type == "int") {
          return fetch_as_matrix<std::int32_t>(sel);
        }
        return fetch_as_matrix<double>(sel);
      },
      _fp.get());
}
