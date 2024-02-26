# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

#' @export RcppHiCFile
#' @export RcppMultiResolutionFile
#' @export RcppSingleCellFile

#' @export File
#' @export MultiResFile
#' @export SingleCellFile

#' @export fetch

#' @export hictkR_open

loadModule(module = "hictkR", TRUE)

#' Open a .hic or .cool file for reading
#'
#' @param path path to the file to be opened (Cooler URI syntax is supported).
#' @param resolution matrix resolution. Required when file is in .hic format.
#' @param matrix_type type of the matrix to be opened. Should be one of "observed", "oe" or "expected".
#' @param matrix_unit unit of the matrix to be opened. Should be one of "BP", "FRAG".
#' @returns a file handle.
#' @examples
#' \dontrun{
#' File("interactions.cool")
#' File("interactions.mcool::/resolutions/100000")
#' File("interactions.mcool", 100000)
#' File("interactions.hic", 100000)
#' }

File <-
  function(path,
           resolution = NULL,
           matrix_type = "observed",
           matrix_unit = "BP") {
    if (is.null(resolution)) {
      resolution <- 0
    }
    return(new(RcppHiCFile, path, resolution, matrix_type, matrix_unit))
  }

#' Opena a .mcool file for reading
#'
#' @param path path to the file to be opened.
#' @returns a file handle.
#' @examples
#' \dontrun{
#' MultiResolutionFile("interactions.mcool")
#' }

MultiResFile <- function(path) {
  return(new(RcppMultiResFile, path))
}

#' Opena a .scool file for reading
#'
#' @param path path to the file to be opened.
#' @returns a file handle.
#' @examples
#' \dontrun{
#' SingleCellFile("interactions.scool")
#' }

SingleCellFile <- function(path) {
  return(new(RcppSingleCellFile, path))
}


#' Fetch interactions from a File object
#'
#' @param file file from which interactions should be fetched.
#' @param range1 first set of genomic coordinates of the region to be queried.
#'               Accepted formats are UCSC or BED format.
#'               When not provided, genome-wide interactions will be returned.
#' @param range2 second set of genomic coordinates of the region to be queried.
#'               When not provided, range2 is assumed to be identical to range1.
#' @param normalization name of the normalization factors used to balance interactions.
#'                      Specify "NONE" to return raw interactions.
#' @param count_type data type used to fetch interactions.
#'                   Should be "int" or "float"
#' @param join join genomic coordinates onto pixels.
#'             When TRUE, interactions will be returned in bedgraph2 format.
#'             When FALSE, interactions will be returned in COO format.
#'             Ignored when type="dense".
#' @param query_type type of the queries provided through range1 and range2 parameters.
#'                   Types of query supported: "UCSC", "BED".
#' @param type interactions format.
#'             Supported formats: "df", "dense".
#' @returns a DataFrame or Matrix object with the interactions for the given query.
#' @examples
#' \dontrun{
#' f <- File("interactions.hic",
#'           1000000)
#' fetch(f)                             # Fetch genome-wide interactions
#' fetch(f, "chr2L")                    # Fetch interactions overlapping a symmetric query
#' fetch(f,
#'       "chr2L:0-10,000,000",
#'       "chr3L:10,000,000-20,000,000") # Fetch interactions overlapping an asymmetric query
#' fetch(f, normalization="ICE")        # Fetch ICE-normalized interactions
#' fetch(f, join=TRUE)                  # Fetch interactions together with their genomic coordinates
#' fetch(f,
#'       "chr1\t0\t10000000",
#'       query_type="BED")              # Fetch interactions given a query in BED format
#' fetch(f, type="dense")               # Fetch interactions in dense format (i.e. as a Matrix)
#' }

fetch <-
  function(file,
           range1 = "",
           range2 = "",
           normalization = "NONE",
           count_type = "int",
           join = FALSE,
           query_type = "UCSC",
           type = "df") {
    if (type == "df") {
      return(file$fetch_df(range1, range2, normalization, count_type, join, query_type))
    }

    if (type == "dense") {
      return(file$fetch_dense(range1, range2, normalization, count_type, query_type))
    }
  }

#' Open files in .cool, .mcool, .scool, and .hic format

#' @param path path to the file to be opened (Cooler URI syntax is supported).
#' @param resolution resolution of the file to be opened.
#'                   Required when file is in .hic format.
#' @param cell name of the cell to be opened.
#'             Ignored when file is not in .scool format.
#' @returns a file handle of the appropriate type.
#' @examples
#' \dontrun{
#' hictkR_open("interactions.cool")
#' hictkR_open("interactions.mcool")
#' hictkR_open("interactions.scool")
#' hictkR_open("interactions.mcool", resolution=10000)
#' hictkR_open("interactions.hic", resolution=10000)
#' hictkR_open("interactions.scool", cell="id_0001")
#' }

hictkR_open <- function(path,
                        resolution = NULL,
                        cell = NULL) {
  if ("path" %in% names(path)) {
    # Assume path is actually an .cool, .mcool, .scool or .hic file
    path <- path$path
  }

  if ("resolution" %in% names(path)) {
    # Assume path is actually .cool, .scool or .hic file
    resolution <- path$resolution
  }

  if (!is.null(resolution)) {
    resolution <- as.integer(resolution)
  }


  if (is_multires_file(path)) {
    if (is.null(resolution)) {
      return(MultiResolutionFile(path))
    }
    uri <- paste(path, "::/resolutions/", resolution, sep = "")
    return(File(uri))
  }

  if (is_scool_file(path)) {
    if (!is.null(resolution)) {
      warning("resolution is ignored when file is in .scool format.")
    }

    if (is.null(cell)) {
      return(SingleCellFile(path))
    }

    uri <- paste(path, "::/cells/", cell, sep = "")
    return(File(uri))
  }

  if (is_hic_file(path) && is.null(resolution)) {
    stop("resolution is required when file is in .hic format.")
  }

  return(File(path, resolution))
}

#' Test whether a file is in .cool format
#'
#' @param path path to the file to be tested (Cooler URI syntax is supported).

is_cooler <- function(path) {
  return(Rcpp_is_cooler(path))
}

#' Test whether a file is in .mcool format
#'
#' @param path path to the file to be tested.

is_multires_file <- function(path) {
  return(Rcpp_is_multires_file(path))
}

#' Test whether a file is in .cool format
#'
#' @param path path to the file to be tested.

is_scool_file <- function(path) {
  return(Rcpp_is_scool_file(path))
}

#' Test whether a file is in .cool format
#'
#' @param path path to the file to be tested.

is_hic_file <- function(path) {
  return(Rcpp_is_hic_file(path))
}
