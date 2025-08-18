<!--
Copyright (C) 2025 Roberto Rossini <roberros@uio.no>

SPDX-License-Identifier: GPL-2.0-or-later

This library is free software: you can redistribute it and/or
modify it under the terms of the GNU Public License as published
by the Free Software Foundation; either version 3 of the License,
or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Library General Public License for more details.

You should have received a copy of the GNU Public License along
with this library.  If not, see
<https://www.gnu.org/licenses/>.
-->

# hictkR

---

<!-- markdownlint-disable MD033 -->

<table>
    <tr>
      <td>Downloads</td>
      <td>
        <a href="https://doi.org/10.5281/zenodo.10991042">
          <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.10991042.svg" alt="Zenodo">
        </a>
      </td>
    </tr>
    <tr>
      <td>Documentation</td>
      <td>
        <a href="https://paulsengroup.github.io/hictkR">
          <img src="https://img.shields.io/badge/docs-passing-green" alt="Documentation">
        </a>
      </td>
    </tr>
    <tr>
      <td>License</td>
      <td>
        <a href="https://github.com/paulsengroup/hictkR/blob/main/LICENSE">
          <img src="https://img.shields.io/badge/License-GPL%202.0%20or%20later-green" alt="License">
        </a>
      </td>
    </tr>
    <tr>
      <td>CI</td>
      <td>
        <a href="https://github.com/paulsengroup/hictkR/actions/workflows/ci.yml">
          <img src="https://github.com/paulsengroup/hictkR/actions/workflows/ci.yml/badge.svg" alt="CI Status">
        </a>
        &nbsp
        <a href="https://github.com/paulsengroup/hictkR/actions/workflows/r-build.yml">
          <img src="https://github.com/paulsengroup/hictkR/actions/workflows/r-build.yml/badge.svg" alt="R build Status">
        </a>
        &nbsp
        <a href="https://github.com/paulsengroup/hictkR/actions/workflows/pkgdown.yml">
          <img src="https://github.com/paulsengroup/hictkR/actions/workflows/pkgdown.yml/badge.svg" alt="Pkgdown build Status">
        </a>
      </td>
    </tr>
</table>

<!-- markdownlint-enable MD033 -->

---

R bindings for [hictk](https://github.com/paulsengroup/hictk), a blazing fast toolkit to work with .hic and .cool files.

If you are looking for the Python API, checkout the [hictkpy](https://github.com/paulsengroup/hictkpy) repository.

## Installing hictkR

hictkR can be installed from CRAN or from GitHub using `devtools`:

```r
# Install from CRAN
install.packages("hictkR")

# Install from GitHub
install.packages("devtools")
devtools::install_github("paulsengroup/hictkR@v0.1.0")
```

hictkR contains extensions written in C++ that need to be compiled before hictkR itself is installed.

This requires a compiler toolchain supporting C++17, such as:

- GCC 8+
- Clang 8+
- Apple-Clang 10.0+

On Windows a suitable compiler toolchain can be installed using [Rtools](https://cran.r-project.org/bin/windows/Rtools/).

<details>
<summary>More details about the build process</summary>

hictkR depends on the [libhictk](https://github.com/paulsengroup/hictk), the C++ library that underlies hictk.

libhictk is a header-only library that depends on several third-party packages, such as `boost` and `HDF5`.

Instead of requiring users to manually install all the required dependencies, `hictkR` comes with a
[configure](https://github.com/paulsengroup/hictkR/blob/main/configure)
(and [configure.win](https://github.com/paulsengroup/hictkR/blob/main/configure.win))
script that download, configure, and build the required dependencies using [Conan](https://conan.io/).

In brief, here is what the script does:

- Setup a temporary folder inside the package build folder.\
  All temporary files are created inside this folder, which is automatically deleted after `hictkR` has been successfully installed
- Generate a `cleanup` script to remove build artifacts when calling e.g. `devtools::install(args=c("--clean"))`
- Download `uv` from [astral.sh](https://astral.sh/)
- Use `uv` to create an environment with `conan`, `cmake`, and `ninja`.\
  If a modern version of `Python` is not available on the host machine, then `uv` will first download and install `Python` inside the temporary folder.\
  `Python` is required to run `Conan`
- Configure `Conan` such that all build artifacts are stored inside the package temporary folder
- Run script [tools/generate_makevars.py](https://github.com/paulsengroup/hictkR/blob/main/tools/generate_makevars.py) to do the following:
  - Use `Conan` to build `hictk` and all of its dependencies (see [tools/conanfile.py](https://github.com/paulsengroup/hictkR/blob/main/tools/conanfile.py))\
    Special care has been taken to ensure that only necessary dependencies are built.\
    For example, while `hictk` depends on `boost`, it only requires a handful of its components (most of which are header-only).\
    Thus, `Conan` is instructed to only build `boost` modules that are strictly needed
  - Generate a `Makevars` file with the appropriate include paths and link flags, such that the `R` build system can find `hictk` and all of its dependencies

Once the `Makevars` has been generated, it is placed inside `src/`, and the rest of the build process is driven by `R`'s build system.

On Windows, there's an additional step to build [b2](https://www.boost.org/doc/libs/1_89_0/tools/build/), which is required to build `boost`.\
`Conan` is supposed to install, and if necessary, build `b2`, but this does not work in the `Rtools` build environment.

You can customize where temporary files are placed using the following two environment variables:

- `HICTKR_TMPDIR`: this is where all temporary files generated by the `configure` script are stored
- `HICTKR_CONAN_HOME`: this is used to set the `CONAN_HOME` variable, where all build files generate by `Conan` are stored.\
  If you are debugging build failures, it may be a good idea to set this variable, such that `Conan` does not have to build all of the dependency from scratch every time

Finally, `Conan` is configured to preferentially use the `C` and `C++` compilers set through the `CC` and `CXX` environment variables.\
Thus, on Linux and macOS, we recommend setting these variables to the same compiler used by `R`.

</details>

## Using hictkR

```r
library(hictkR)

path <- "file.mcool"  # "file.hic"
f <- File(path, resolution=100000)

df <- fetch(f, "chr1:0-10,000,000", "chr2:0-20,000,000", join=TRUE)
df
```

| chrom1 | start1 | end1   | chrom2 | start2 | end2   | count |
| ------ | ------ | ------ | ------ | ------ | ------ | ----- |
| chr1   | 0      | 100000 | chr2   | 0      | 100000 | 15    |
| chr1   | 0      | 100000 | chr2   | 100000 | 200000 | 5     |
| chr1   | 0      | 100000 | chr2   | 300000 | 400000 | 17    |
| chr1   | 0      | 100000 | chr2   | 400000 | 500000 | 22    |
| chr1   | 0      | 100000 | chr2   | 500000 | 600000 | 30    |
| chr1   | 0      | 100000 | chr2   | 600000 | 700000 | 21    |
| chr1   | 0      | 100000 | chr2   | 600000 | 700000 | 21    |
| ...    | ...    | ...    | ...    | ...    | ...    | ...   |

Refer to the [manual](https://paulsengroup.github.io/hictkR/reference/index.html) and [vignette](https://paulsengroup.github.io/hictkR/articles/hictkR-vignette.html) available at
[paulsengroup.github.io/hictkR](https://paulsengroup.github.io/hictkR/) for more examples on how to use hictkR.

## Citing

If you use hictkR in you research, please cite the following publication:

Roberto Rossini, Jonas Paulsen, hictk: blazing fast toolkit to work with .hic and .cool files
_Bioinformatics_, Volume 40, Issue 7, July 2024, btae408, [https://doi.org/10.1093/bioinformatics/btae408](https://doi.org/10.1093/bioinformatics/btae408)

<details>
<summary>BibTex</summary>

```bibtex
@article{hictk,
    author = {Rossini, Roberto and Paulsen, Jonas},
    title = "{hictk: blazing fast toolkit to work with .hic and .cool files}",
    journal = {Bioinformatics},
    volume = {40},
    number = {7},
    pages = {btae408},
    year = {2024},
    month = {06},
    issn = {1367-4811},
    doi = {10.1093/bioinformatics/btae408},
    url = {https://doi.org/10.1093/bioinformatics/btae408},
    eprint = {https://academic.oup.com/bioinformatics/article-pdf/40/7/btae408/58385157/btae408.pdf},
}
```

</details>
