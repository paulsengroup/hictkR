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
devtools::install_github("paulsengroup/hictkR")
```

## Using hictkR

```r
library(hictkR)

path <- "file.mcool"  # "file.hic"
f <- File(path, resolution=100000)

df <- fetch(f, "chr1:0-10,000,000", "chr2:0-20,000,000", join=TRUE)
df
```

| chrom1 | start1  | end1   | chrom2 | start2  | end2    | count |
|--------|---------|--------|--------|---------|---------|-------|
| chr1   | 0       | 100000 | chr2   | 0       | 100000  | 15    |
| chr1   | 0       | 100000 | chr2   | 100000  | 200000  | 5     |
| chr1   | 0       | 100000 | chr2   | 300000  | 400000  | 17    |
| chr1   | 0       | 100000 | chr2   | 400000  | 500000  | 22    |
| chr1   | 0       | 100000 | chr2   | 500000  | 600000  | 30    |
| chr1   | 0       | 100000 | chr2   | 600000  | 700000  | 21    |
| chr1   | 0       | 100000 | chr2   | 600000  | 700000  | 21    |
| ...    | ...     | ...    | ...    | ...     | ...     | ...   |

Refer to the manual and vignettes for more examples on how to use hictkR.

## Citing

If you use hictkR in you reaserch, please cite the following publication:

Roberto Rossini, Jonas Paulsen hictk: blazing fast toolkit to work with .hic and .cool files.
_bioRxiv_ __2023.11.26.568707__. [https://doi.org/10.1101/2023.11.26.568707](https://doi.org/10.1101/2023.11.26.568707)

<details>
<summary>BibTex</summary>

```bibtex
@article {hictk,
	author = {Roberto Rossini and Jonas Paulsen},
	title = {hictk: blazing fast toolkit to work with .hic and .cool files},
	elocation-id = {2023.11.26.568707},
	year = {2023},
	doi = {10.1101/2023.11.26.568707},
	publisher = {Cold Spring Harbor Laboratory},
	URL = {https://www.biorxiv.org/content/early/2023/11/27/2023.11.26.568707},
	eprint = {https://www.biorxiv.org/content/early/2023/11/27/2023.11.26.568707.full.pdf},
	journal = {bioRxiv}
}
```

</details>
