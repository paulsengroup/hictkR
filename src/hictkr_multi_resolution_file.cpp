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

#include "./hictkr_multi_resolution_file.h"

#include <string>

#include "./common.h"

MultiResFile::MultiResFile(std::string path) : _fp(std::move(path)) {}

std::string MultiResFile::path() const { return _fp.path(); }

Rcpp::DataFrame MultiResFile::chromosomes() const { return get_chromosomes(_fp); }

Rcpp::IntegerVector MultiResFile::resolutions() const {
  return {_fp.resolutions().begin(), _fp.resolutions().end()};
}
