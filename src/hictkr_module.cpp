#include "./hictkr_file.hpp"
#include <Rcpp.h>

RCPP_MODULE(hictkR) {

  Rcpp::class_<HiCFile>("HiCFile")
      .constructor<std::string, std::uint32_t, std::string, std::string>()
      .property("is_cooler", &HiCFile::is_cooler)
      .property("is_hic", &HiCFile::is_hic)
      .property("path", &HiCFile::path, "Path to the opened file.")
      .property("nbins", &HiCFile::nbins, "Number of bins.")
      .method("fetch_df", &HiCFile::fetch_df,
              "Fetch interactions as a DataFrame.")
      .method("fetch_dense", &HiCFile::fetch_dense,
              "Fetch interactions as a Matrix.");
}
