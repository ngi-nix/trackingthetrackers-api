{
  description = "Tracking The Trackers - API to submit APKs for testing.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix-src.url = "github:DavHau/mach-nix";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src }:
    flake-utils.lib.eachDefaultSystem
      (
        system:
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
            }
      ) // {
      # start the uvicorn service, possibly an nginx proxy as well if
      # reverse-proxy.enabled = true;
      nixosModules = {
        ttapi = (
          { config, lib, pkgs, ... }:
            let
              # TODO deal with secret
              ttapi_secret_cfg = pkgs.writeText "ttapi-secrets"
                (
                  lib.generators.toKeyValue {} {
                    TTAPI_DB_PASSWORD = "foobar";
                    TTAPI_USER_PASSWORD = "foobar";
                  }
                );
              cfg = config.services.ttapi-server;
            in
              {
                options = {
                  services.ttapi-server = {
                    enable = lib.mkOption {
                      default = false;
                      type = lib.types.bool;
                      description = ''
                        Enable Tracking the Trackers API service.
                      '';
                    };
                  };
                };

                config = {
                  services.postgresql = {
                    enable = lib.mkIf cfg.enable true;
                    ensureDatabases = [ "bincache" ];
                    ensureUsers = [
                      {
                        name = "ttapi";
                        ensurePermissions = { "DATABASE bincache" = "ALL PRIVILEGES"; };
                      }
                    ];
                  };
                  systemd.services.ttapi-server = {
                    description = "Tracking the Trackers API service";
                    wantedBy = lib.mkIf cfg.enable [ "multi-user.target" ];
                    after = [ "network.target" "postgresql.service" ];
                    script = ''
                      ${self.packages.python}/bin/uvicorn server:app
                    '';
                  };
                  systemd.services.ttapi-setup = {
                    script = ''
                      # Setup the db
                      set -eu
                      ${pkgs.utillinux}/bin/runuser -u ${config.services.postgresql.superUser} -- \
                        ${config.services.postgresql.package}/bin/psql -c \
                        " ALTER ROLE '$TTAPI_DB_USER' WITH PASSWORD '$TTAPI_DB_PASSWORD' "
                    '';

                    after = [ " postgresql.service " ];
                    requires = [ " postgresql.service " ];
                    before = [ " ttapi-server.service " ];
                    requiredBy = [ " ttapi-server.service " ];
                    serviceConfig.EnvironmentFile = ttapi_secret_cfg;
                  };
                };
              }
        );
      };
      nixosConfigurations.container = nixpkgs.lib.nixosSystem { system = " x86_64-linux "; modules = [ self.nixosModules.ttapi ({ pkgs, ... }: { system.configurationRevision = self.rev or " dirty "; networking.hostName = " ttapi "; networking.firewall.allowedTCPPorts = [ 8000 ]; services.getty.autologinUser = " root "; }) ]; };
    };
}
