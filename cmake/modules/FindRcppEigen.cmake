# FindRcppEigen.cmake
# - Try to find RcppEigen
#
# The following variables are optionally searched for defaults
#  RcppEigen_ROOT_DIR:  Base directory where all RcppEigen components are found
#
# Once done this will define
#  RcppEigen_FOUND - System has RcppEigen
#  RcppEigen_INCLUDE_DIRS - The RcppEigen include directories
#  RcppEigen_LIBRARIES - The libraries needed to use RcppEigen

#set(RcppEigen_ROOT_DIR "" CACHE PATH "Folder containing RcppEigen")

if (NOT R_FOUND)
  find_package(R REQUIRED)
endif ()

# ask R for the package directories
if (NOT LIBR_PACKAGE_DIRS)
  execute_process(
          COMMAND ${R_COMMAND} "--slave" "--no-save" "-e" " cat(paste(.libPaths(), sep='', collapse=';'))"
          OUTPUT_VARIABLE LIBR_PACKAGE_DIRS
  )
  if (LIBR_PACKAGE_DIRS)
    message(STATUS "Detected R package library directories: ${LIBR_PACKAGE_DIRS}")
  endif ()
endif ()

find_path(RcppEigen_INCLUDE_DIR "RcppEigen.h"
        PATHS ${RcppEigen_ROOT_DIR} ${LIBR_PACKAGE_DIRS} /usr/lib/R/site-library/RcppEigen /usr/lib64/R/library/RcppEigen
        PATH_SUFFIXES include RcppEigen/include
        NO_DEFAULT_PATH)
find_package_handle_standard_args(RcppEigen REQUIRED_VARS RcppEigen_INCLUDE_DIR)
if (RcppEigen_FOUND)
  set(RcppEigen_INCLUDE_DIRS ${RcppEigen_INCLUDE_DIR})
  mark_as_advanced(RcppEigen_INCLUDE_DIR)
endif ()

add_library(rcpp_eigen INTERFACE)
target_include_directories(rcpp_eigen SYSTEM INTERFACE ${R_INCLUDE_DIRS} ${RcppEigen_INCLUDE_DIRS})
target_link_libraries(rcpp_eigen INTERFACE -Wl,--start-group ${R_LIBRARIES} -Wl,--end-group)
