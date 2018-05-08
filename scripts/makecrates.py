"""
makecrates.py
Copyright 2017 Adam Greig
Licensed under the MIT and Apache 2.0 licenses.

Autogenerate the crate Cargo.toml and src/lib.rs file based on available
YAML files for each STM32 family.

Usage: python3 scripts/makecrates.py devices/
"""

import os
import sys
import glob
import os.path

VERSION = "0.1.1"

CARGO_TOML_TPL = """\
[package]
name = "{crate}"
version = "{version}"
authors = ["Adam Greig <adam@adamgreig.com>"]
description = "Device support crates for {family} devices"
repository = "https://github.com/adamgreig/stm32-rs"
readme = "README.md"
keywords = ["stm32", "svd2rust", "no_std", "embedded"]
categories = ["embedded", "no-std"]
license = "MIT/Apache-2.0"

[dependencies]
bare-metal = "0.1.1"
vcell = "0.1.0"
cortex-m = "0.4.3"
cortex-m-rt = "0.4.0"

[features]
default = []
rt = []
{features}
"""

SRC_LIB_RS_TPL = """\
//! Peripheral access API for {family} microcontrollers
//! (generated using [svd2rust])
//! [svd2rust]: https://github.com/japaric/svd2rust
//!
//! You can find an overview of the API here:
//! https://docs.rs/svd2rust/0.8.1/svd2rust/#peripheral-api
//!
//! For more details see the README here:
//! https://github.com/adamgreig/stm32-rs

#![allow(non_camel_case_types)]
#![allow(private_no_mangle_statics)]
#![feature(const_fn)]
#![feature(try_from)]
#![no_std]

#![cfg_attr(feature = "rt", feature(global_asm))]
#![cfg_attr(feature = "rt", feature(use_extern_macros))]
#![cfg_attr(feature = "rt", feature(used))]

extern crate vcell;
extern crate bare_metal;
extern crate cortex_m;

#[cfg(feature = "rt")]
extern crate cortex_m_rt;
#[cfg(feature = "rt")]
pub use cortex_m_rt::{{default_handler, exception}};

{mods}
"""

README_TPL = """\
# {crate}
This crate provides an autogenerated API for access to {family} peripherals.
The API is generated using [svd2rust] with patched svd files containing
extensive type-safe support. For more information please see the [main repo].

[svd2rust]: https://github.com/japaric/svd2rust
[main repo]: https://github.com/adamgreig/stm32-rs

## Usage
Each device supported by this crate is behind a feature gate so that you only
compile the device(s) you want. To use, in your Cargo.toml:

```toml
[dependencies.{crate}]
version = "{version}"
features = ["{device}", "rt"]
```

The `rt` feature is optional and brings in support for `cortex-m-rt`.

For details on the autogenerated API, please see:
https://docs.rs/svd2rust/0.8.1/svd2rust/#peripheral-api

## Supported Devices

{devices}
"""


def make_features(devices):
    return "\n".join("{} = []".format(d) for d in sorted(devices))


def make_mods(devices):
    return "\n".join('#[cfg(feature = "{0}")]\npub mod {0};\n'.format(d)
                     for d in sorted(devices))


def main():
    devices = {}

    for path in glob.glob(os.path.join(sys.argv[1], "*.yaml")):
        yamlfile = os.path.basename(path)
        family = yamlfile[:7]
        device = os.path.splitext(yamlfile)[0].lower()
        if family not in devices:
            devices[family] = []
        devices[family].append(device)

    dirs = ", ".join(x.lower()+"/" for x in devices)
    print("Going to create/update the following directories:")
    print(dirs)
    input("Enter to continue, ctrl-C to cancel")

    for family in devices:
        devices[family] = sorted(devices[family])
        crate = family.lower()
        features = make_features(devices[family])
        mods = make_mods(devices[family])
        ufamily = family.upper()
        cargo_toml = CARGO_TOML_TPL.format(
            family=ufamily, crate=crate, version=VERSION, features=features)
        readme = README_TPL.format(
            family=ufamily, crate=crate, device=devices[family][0],
            version=VERSION,
            devices="\n".join("* " + d.upper().replace("X", "x")
                              for d in devices[family]))
        lib_rs = SRC_LIB_RS_TPL.format(family=ufamily, mods=mods)

        os.makedirs(os.path.join(crate, "src"), exist_ok=True)
        with open(os.path.join(crate, "Cargo.toml"), "w") as f:
            f.write(cargo_toml)
        with open(os.path.join(crate, "README.md"), "w") as f:
            f.write(readme)
        with open(os.path.join(crate, "src", "lib.rs"), "w") as f:
            f.write(lib_rs)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <yaml directory>".format(sys.argv[0]))
        sys.exit(1)
    else:
        main()
