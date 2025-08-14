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
#include <hictk/multires_file.hpp>
#include <string>

class MultiResFile {
  hictk::MultiResFile _fp;

 public:
  explicit MultiResFile(std::string path);

  [[nodiscard]] std::string path() const;
  [[nodiscard]] Rcpp::DataFrame chromosomes() const;
  [[nodiscard]] Rcpp::IntegerVector resolutions() const;
};
