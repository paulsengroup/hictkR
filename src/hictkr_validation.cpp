// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#include "./hictkr_validation.hpp"

#include <hictk/cooler/validation.hpp>
#include <hictk/hic/validation.hpp>

bool is_cooler(std::string path) { return !!hictk::cooler::utils::is_cooler(path); }
bool is_multires_file(std::string path) { return !!hictk::cooler::utils::is_multires_file(path); }
bool is_scool_file(std::string path) { return !!hictk::cooler::utils::is_scool_file(path); }
bool is_hic_file(std::string path) { return !!hictk::hic::utils::is_hic_file(path); }
