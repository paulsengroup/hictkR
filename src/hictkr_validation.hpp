// Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
//
// SPDX-License-Identifier: MIT

#pragma once

#include <string>

[[nodiscard]] bool is_cooler(std::string path);
[[nodiscard]] bool is_multires_file(std::string path);
[[nodiscard]] bool is_scool_file(std::string path);
[[nodiscard]] bool is_hic_file(std::string path);
