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

#include "./hictkr_file.h"

// clang-format on
#include <Rcpp.h>

#include "./RcppEigen/RcppEigen.h"
// clang-format off

#include <arrow/c/abi.h>
#include <arrow/c/bridge.h>
#include <arrow/table.h>
#include <fmt/format.h>

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <hictk/balancing/methods.hpp>
#include <hictk/bin_table.hpp>
#include <hictk/cooler/cooler.hpp>
#include <hictk/genomic_interval.hpp>
#include <hictk/hic.hpp>
#include <hictk/transformers/join_genomic_coords.hpp>
#include <hictk/transformers/to_dataframe.hpp>
#include <hictk/transformers/to_dense_matrix.hpp>
#include <limits>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
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

template <typename N, typename PixelSelector>
[[nodiscard]] static std::shared_ptr<arrow::Table> make_bg2_arrow_df(
    const PixelSelector &sel, hictk::transformers::QuerySpan span,
    std::optional<std::uint64_t> diagonal_band_width) {
  if constexpr (std::is_same_v<N, long double>) {
    return make_bg2_arrow_df<double>(sel, span, diagonal_band_width);
  } else {
    return hictk::transformers::ToDataFrame(
        sel, sel.template end<N>(), hictk::transformers::DataFrameFormat::BG2, sel.bins_ptr(), span,
        false, 256'000, diagonal_band_width)();
  }
}

template <typename N, typename PixelSelector>
[[nodiscard]] static std::shared_ptr<arrow::Table> make_coo_arrow_df(
    const PixelSelector &sel, hictk::transformers::QuerySpan span,
    std::optional<std::uint64_t> diagonal_band_width) {
  if constexpr (std::is_same_v<N, long double>) {
    return make_coo_arrow_df<double>(sel, span, diagonal_band_width);
  } else {
    return hictk::transformers::ToDataFrame(
        sel, sel.template end<N>(), hictk::transformers::DataFrameFormat::COO, sel.bins_ptr(), span,
        false, 256'000, diagonal_band_width)();
  }
}

static void arrow_schema_deleter(ArrowSchema *schema) noexcept {
  try {
    if (schema->release) {
      schema->release(schema);
    }
    free(schema);
  } catch (...) {  // NOLINT
  }
}

static void arrow_array_stream_deleter(ArrowArrayStream *stream) noexcept {
  try {
    if (stream->release) {
      stream->release(stream);
    }
    free(stream);
  } catch (...) {  // NOLINT
  }
}

using ArrowSchemaXPtr = Rcpp::XPtr<ArrowSchema, Rcpp::PreserveStorage, arrow_schema_deleter>;
using ArrowArrayStreamXPtr =
    Rcpp::XPtr<ArrowArrayStream, Rcpp::PreserveStorage, arrow_array_stream_deleter>;

[[nodiscard]] static ArrowSchemaXPtr export_arrow_schema(
    const std::shared_ptr<arrow::Schema> &schema_in) {
  auto *schema = static_cast<ArrowSchema *>(malloc(sizeof(ArrowSchema)));
  if (!schema) {
    throw std::bad_alloc();
  }

  const auto status = arrow::ExportSchema(*schema_in, schema);
  if (!status.ok()) {
    free(schema);
    throw std::runtime_error(fmt::format(
        FMT_STRING("Failed to export arrow::Schema as ArrowSchema: {}"), status.message()));
  }

  ArrowSchemaXPtr ptr{schema, true};
  ptr.attr("class") = "nanoarrow_schema";
  return ptr;
}

[[nodiscard]] static ArrowArrayStreamXPtr export_arrow_array_stream(
    std::shared_ptr<arrow::ChunkedArray> column, const ArrowSchemaXPtr &schema) {
  auto *array_stream = static_cast<ArrowArrayStream *>(malloc(sizeof(ArrowArrayStream)));
  if (!array_stream) {
    throw std::bad_alloc();
  }

  const auto status = arrow::ExportChunkedArray(std::move(column), array_stream);
  if (!status.ok()) {
    free(array_stream);
    throw std::runtime_error(
        fmt::format(FMT_STRING("Failed to export arrow::ChunkedArray as ArrowArrayStream: {}"),
                    status.message()));
  }

  ArrowArrayStreamXPtr ptr{array_stream, true};
  ptr.attr("class") = "nanoarrow_array_stream";
  ptr.attr("schema") = schema;
  return ptr;
}

[[nodiscard]] static Rcpp::DataFrame arrow_table_to_df(
    const std::shared_ptr<arrow::Table> &arrow_table) {
  assert(arrow_table);

  auto schema_r = export_arrow_schema(arrow_table->schema());
  const auto col_names = arrow_table->ColumnNames();

  Rcpp::List columns_r(arrow_table->num_columns());

  auto nanoarrow = Rcpp::Environment::namespace_env("nanoarrow");
  const Rcpp::Function nanoarrow_convert_array_stream{nanoarrow["convert_array_stream"]};

  for (R_xlen_t i = 0; i < columns_r.size(); ++i) {
    columns_r[i] = nanoarrow_convert_array_stream(export_arrow_array_stream(
        arrow_table->column(hictk::conditional_static_cast<int>(i)), schema_r));
  }

  columns_r.attr("names") = Rcpp::CharacterVector(col_names.begin(), col_names.end());

  auto base = Rcpp::Environment::base_namespace();
  const Rcpp::Function as_data_frame = base["as.data.frame"];

  return as_data_frame(columns_r);
}

template <typename N, bool join, typename PixelSelector>
[[nodiscard]] static Rcpp::DataFrame make_df(
    const PixelSelector &sel,
    hictk::transformers::QuerySpan span = hictk::transformers::QuerySpan::upper_triangle,
    std::optional<std::uint64_t> diagonal_band_width = {}) {
  if constexpr (join) {
    return arrow_table_to_df(make_bg2_arrow_df<N>(sel, span, diagonal_band_width));
  } else {
    return arrow_table_to_df(make_coo_arrow_df<N>(sel, span, diagonal_band_width));
  }
}

[[nodiscard]] static hictk::balancing::Method to_hictk_normalization_method(
    const Rcpp::Nullable<Rcpp::String> &name) {
  if (name.isNull() || Rcpp::as<Rcpp::String>(name) == "NONE") {
    return hictk::balancing::Method::NONE();
  }
  return hictk::balancing::Method{Rcpp::as<std::string>(name)};
}

Rcpp::DataFrame HiCFile::fetch_df(Rcpp::Nullable<Rcpp::String> range1,
                                  Rcpp::Nullable<Rcpp::String> range2,
                                  Rcpp::Nullable<Rcpp::String> normalization,
                                  std::string count_type, bool join, std::string query_type) const {
  const auto normalization_method = to_hictk_normalization_method(normalization);
  if (normalization_method != "NONE") {
    count_type = "float";
  }

  if (range1.isNull()) {
    assert(range2.isNull());
    return std::visit(
        [&](const auto &ff) {
          auto sel = ff.fetch(normalization_method);
          if (count_type == "int") {
            return join ? make_df<std::int32_t, true>(sel) : make_df<std::int32_t, false>(sel);
          }
          return join ? make_df<double, true>(sel) : make_df<double, false>(sel);
        },
        _fp.get());
  }

  const auto qt =
      query_type == "UCSC" ? hictk::GenomicInterval::Type::UCSC : hictk::GenomicInterval::Type::BED;

  return std::visit(
      [&](const auto &ff) {
        auto sel = range2.isNull() || range1 == range2
                       ? ff.fetch(Rcpp::as<std::string>(range1), normalization_method, qt)
                       : ff.fetch(Rcpp::as<std::string>(range1), Rcpp::as<std::string>(range2),
                                  normalization_method, qt);
        if (count_type == "int") {
          return join ? make_df<std::int32_t, true>(sel) : make_df<std::int32_t, false>(sel);
        }
        return join ? make_df<double, true>(sel) : make_df<double, false>(sel);
      },
      _fp.get());
}

template <typename N, typename PixelSelector,
          typename RcppMatrixT =
              std::conditional_t<std::is_integral_v<N>, Rcpp::IntegerMatrix, Rcpp::NumericMatrix>>
static RcppMatrixT fetch_as_matrix(PixelSelector &&sel) {
  return Rcpp::wrap(hictk::transformers::ToDenseMatrix(std::move(sel), N{})());
}

Rcpp::RObject HiCFile::fetch_dense(Rcpp::Nullable<Rcpp::String> range1,
                                   Rcpp::Nullable<Rcpp::String> range2,
                                   Rcpp::Nullable<Rcpp::String> normalization,
                                   std::string count_type, std::string query_type) const {
  const auto normalization_method = to_hictk_normalization_method(normalization);
  if (normalization_method != "NONE") {
    count_type = "float";
  }

  if (range1.isNull()) {
    assert(range2.isNull());
    return std::visit(
        [&](const auto &ff) -> Rcpp::RObject {
          auto sel = ff.fetch(normalization_method);
          if (count_type == "int") {
            return fetch_as_matrix<std::int64_t>(std::move(sel));
          }
          return fetch_as_matrix<double>(std::move(sel));
        },
        _fp.get());
  }

  const auto qt =
      query_type == "UCSC" ? hictk::GenomicInterval::Type::UCSC : hictk::GenomicInterval::Type::BED;

  return std::visit(
      [&](const auto &ff) -> Rcpp::RObject {
        auto sel = range2.isNull() || range1 == range2
                       ? ff.fetch(Rcpp::as<std::string>(range1), normalization_method, qt)
                       : ff.fetch(Rcpp::as<std::string>(range1), Rcpp::as<std::string>(range2),
                                  normalization_method, qt);
        if (count_type == "int") {
          return fetch_as_matrix<std::int64_t>(std::move(sel));
        }
        return fetch_as_matrix<double>(std::move(sel));
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
