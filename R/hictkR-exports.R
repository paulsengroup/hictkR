# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

#' @export RcppHiCFile
#' @export RcppMultiResolutionFile
#' @export RcppSingleCellFile

#' @export File
#' @export MultiResolutionFile
#' @export SingleCellFile

#' @export fetch
#' @export hictkR_open

loadModule(module = "hictkR", TRUE)

File <- function(path, resolution = NULL, matrix_type = "observed", matrix_unit = "BP") {
    if (is.null(resolution)) {
        resolution <- 0
    }
    return(new(RcppHiCFile, path, resolution, matrix_type, matrix_unit))
}

MultiResolutionFile <- function(path) {
    return(new(RcppMultiResolutionFile, path))
}

SingleCellFile <- function(path) {
    return(new(RcppSingleCellFile, path))
}


fetch <- function(file, range1 = "", range2 = "", normalization = "NONE", count_type = "int", join = FALSE, query_type = "UCSC", type = "df") {
    if (type == "df") {
        return(file$fetch_df(range1, range2, normalization, count_type, join, query_type))
    }

    if (type == "dense") {
        return(file$fetch_dense(range1, range2, normalization, count_type, query_type))
    }
}

hictkR_open <- function(path, resolution = NULL, cell = NULL) {
    if (class(path) == "RcppMultiResolutionFile") {
        if (is.null(resolution)) {
            stop("resolution is required when opening a multi-resolution file.")
        }
        path <- path$path
    }
    if (class(path) == "RcppSingleCellFile") {
        if (is.null(cell)) {
            stop("cell is required when opening a single-cell file.")
        }
        path <- path$path
    }

    if (is_multires_file(path)) {
        if (is.null(resolution)) {
            return(MultiResolutionFile(path))
        }
        uri <- paste(path, "::/resolutions/", resolution, sep="")
        return(File(uri))
    }

    if (is_scool_file(path)) {
        if (!is.null(resolution)) {
            warning("resolution is ignored when file is in .scool format.")
        }

        if (is.null(cell)) {
            return(SingleCellFile(path))
        }

        uri <- paste(path, "::/cells/", cell, sep="")
        return(File(uri))
    }

    if (is_hic_file(path) && is.null(resolution)) {
        stop("resolution is required when file is in .hic format.")
    }

    return(File(path, resolution))
}
