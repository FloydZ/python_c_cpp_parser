{ pkgs ? import <nixpkgs> {} }:
let
  mach-nix = import (builtins.fetchGit {
    url = "https://github.com/DavHau/mach-nix";
    ref = "refs/tags/3.5.0";
  }) {};
  pyEnv = mach-nix.mkPython rec {
    providers._default = "wheel,conda,nixpkgs,sdist";
    requirements = builtins.readFile ./requirements.txt;
  };
in
mach-nix.nixpkgs.mkShell {
  buildInputs = with pkgs; [
    pyEnv

    clang
    gcc
    calc   # needed for `msc` and `ms`
    jq     # needed for `msc` and `ms`

    # needed to compile `MeasureSuite` with `AssemblyLine`
    pkg-config 
    automake
    autoconf
    libtool
    nasm      # needed for testing
  ];

  shellHook = ''
    # ./build.sh
  '';
}
