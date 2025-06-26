{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # These are the packages that will be available in your environment
  buildInputs = [
    pkgs.python311
    pkgs.google-chrome
    pkgs.chromedriver
    pkgs.stdenv.cc.cc.lib
  ];

  # This is a command that will run when the environment is activated.
  # We are setting environment variables to make sure our application can find
  # the Chrome and Chromedriver binaries provided by Nix.
  shellHook = ''
    export CHROME_BIN=${pkgs.google-chrome}/bin/google-chrome
    export CHROMEDRIVER_PATH=${pkgs.chromedriver}/bin/chromedriver
    # The following is needed for some libraries that compile extensions.
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib
  '';
} 