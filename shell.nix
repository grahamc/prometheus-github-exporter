{ pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (pypkgs: [
      pypkgs.prometheus_client
      pypkgs.requests
      pypkgs.black
    ]))
  ];
}
