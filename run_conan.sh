#!/usr/bin/env bash

set -e
set -u
set -o pipefail

if ! command -v conan &> /dev/null; then
  echo "conan could not be found. Please install conan: https://conan.io/downloads"
  exit 1
fi


if [ -f conan-staging/conandeps.mk ]; then
  exit 0
fi

conan profile detect &> /dev/null || true

conan install ../conanfile.txt -s build_type=Release -s compiler.cppstd=17 --output-folder conan-staging --build=missing --update
