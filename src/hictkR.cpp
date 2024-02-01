#include <cstdint>
#include <hictk/file.hpp>
#include <hictk/version.hpp>
#include <string>

// [[Rcpp::export]]
[[nodiscard]] std::string version() {
  return std::string{hictk::config::version::str()};
}

// [[Rcpp::export]]
[[nodiscard]] std::uint64_t nbins(const std::string &path, std::uint32_t resolution) {
  return hictk::File(path, resolution).nbins();
}
