{
  description = "Tracking The Trackers - API to submit APKs for testing.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix-src.url = "github:DavHau/mach-nix";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          mach-nix = import mach-nix-src { inherit pkgs; python = "python38"; };
          requirements = builtins.readFile ./requirements.txt;
        in
        {
          # defaultPackage = self.packages.${system}.${pname};
          packages = { inherit pkgs; };
          devShell = mach-nix.mkPythonShell {
            inherit requirements;
          };
        }) // {
      nixosModules.ttapi = { };
      nixosConfigurations.vm = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          self.nixosModules.ttapi
          ({ config, lib, pkgs, ... }:
            let
              # TODO
              # XXX: Should be passed out-of-band so as to not end-up in the
              # Nix store
              ttapi_secret_cfg = pkgs.writeText "ttapi-secrets"
                (lib.generators.toKeyValue { } {
                  TTAPI_DB_PASSWORD = "foobar";
                  TTAPI_USER_PASSWORD = "foobar";
                });
            in
            {
              system.configurationRevision = self.rev or "dirty";
              services.postgresql = {
                enable = true;
                ensureDatabases = [ "bincache" ];
                ensureUsers = [
                  {
                    name = "ttapi";
                    ensurePermissions = { "DATABASE bincache" = "ALL PRIVILEGES"; };
                  }
                ];
              };

              systemd.services.ttapi-setup = {
                script = ''
                  # Setup the db
                  set -eu
                  ${pkgs.utillinux}/bin/runuser -u ${config.services.postgresql.superUser} -- \
                    ${config.services.postgresql.package}/bin/psql -c \
                    "ALTER ROLE '$TTAPI_DB_USER' WITH PASSWORD '$TTAPI_DB_PASSWORD'"
                '';

                after = [ "postgresql.service" ];
                requires = [ "postgresql.service" ];
                before = [ "ttapi.service" ];
                requiredBy = [ "ttapi.service" ];
                serviceConfig.EnvironmentFile = ttapi_secret_cfg;
              };

              networking.firewall.allowedTCPPorts = [ 8000 ];

              networking.hostName = "ttapi";
              services.getty.autologinUser = "root";
            })
        ];
      };
    };
}

