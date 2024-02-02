# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

#' @export HiCFile
#' @export File
#' @export fetch
#' @export chromosomes
#' @export bins

loadModule(module = "hictkR", TRUE)

File <- function(path, resolution, matrix_type = "observed", matrix_unit = "BP") {
    return(new(HiCFile, path, resolution, matrix_type, matrix_unit))
}

fetch <- function(file, range1 = "", range2 = "", normalization = "NONE", count_type = "int", join = FALSE, query_type = "UCSC", type = "df") {
    if (type == "df") {
        return(file$fetch_df(range1, range2, normalization, count_type, join, query_type))
    }

    if (type == "dense") {
        return(file$fetch_dense(range1, range2, normalization, count_type, query_type))
    }
}

chromosomes <- function(file) {
    return(file$chromosomes);
}

bins <- function(file) {
    return(file$bins);
}
