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

hictkR can be installed directly from GitHubin various ways. The simples method is using pip: `pip install hictkpy`.

```r
install.packages("devtools")
library(devtools)
install_github("paulsengroup/hictkR")
```

## Using hictkR

```r
library(hictkR)

path <- "file.mcool"  # "file.hic"

f <- File(path, resolution=100000)

df <- fetch(f, "chr1:0-10,000,000", "chr2:0-20,000,000", join=TRUE)

df
```

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
