<!--
Copyright (C) 2024 Roberto Rossini <roberros@uio.no>

SPDX-License-Identifier: MIT
-->

# hictkR

[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![CI](https://github.com/paulsengroup/hictkR/actions/workflows/ci.yml/badge.svg)](https://github.com/paulsengroup/hictkR/actions/workflows/ci.yml)

---

R bindings for hictk, a blazing fast toolkit to work with .hic and .cool files.

## Installing hictkR

hictkR can be installed directly from GitHub.

Installing hictkR requires a compiler toolchain supporting C++17, such as:

- GCC 8+
- Clang 8+
- Apple-Clang 10.0+

On Windows a suitable compiler toolchain can be installed using [Rtools](https://cran.r-project.org/bin/windows/Rtools/).

Furthermore, the following tools are required:

- CMake 3.25+
- Conan 2+

Once all the build dependencies have been installed, the package can be installed as follows (note that this may require some time, as this involves the compilation of several packages):

```r
install.packages("devtools")
devtools::install_github("paulsengroup/hictkR@v0.0.3")
```

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

If you use hictkR in you reaserch, please cite the following publication:

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
