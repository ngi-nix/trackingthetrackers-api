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
              # TODO what should be the defaultPackage?
              # defaultPackage = self.packages.${system}.${pname};
              packages = { inherit pkgs; };
              devShell = mach-nix.mkPythonShell {
                inherit requirements;
              };
            }
      ) // {
      nixosModules = {
        ttapi = (
          { config, lib, pkgs, ... }:
            let
              ttapi_secret_cfg = pkgs.writeText "ttapi-secrets"
                (
                  lib.generators.toKeyValue {} {
                    TTAPI_DB_PASSWORD = "bincache";
                    TTAPI_USER_PASSWORD = "bincache";
                  }
                );
              cfg = config.services.ttapi-db;
            in
              {
                options = {
                  services.ttapi-db = {
                    enable = lib.mkOption {
                      default = true;
                      type = lib.types.bool;
                      description = ''
                        Enable and set up schema for Tracking the Trackers API database.
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
                  systemd.services.ttapi-setup = {
                    script = ''
                      # Setup the db
                      set -eu
                      ${pkgs.utillinux}/bin/runuser -u ${config.services.postgresql.superUser} -- \
                        ${config.services.postgresql.package}/bin/psql -c \
                        " ALTER ROLE '$TTAPI_DB_USER' WITH PASSWORD '$TTAPI_DB_PASSWORD' "
                    '';

                    after = [ "postgresql.service" ];
                    requires = [ "postgresql.service" ];
                    before = [ "ttapi-db.service" ];
                    requiredBy = [ "ttapi-db.service" ];
                    serviceConfig.EnvironmentFile = ttapi_secret_cfg;
                  };
                };
              }
        );
      };
      nixosConfigurations.test-vm = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          (
            { modulesPath, pkgs, ... }: {
              imports = [ (modulesPath + "/virtualisation/qemu-vm.nix") ];
            }
          )
          self.nixosModules.ttapi
          (
            { config, lib, pkgs, ... }: {
              system.configurationRevision = self.rev or "dirty";
              virtualisation = {
                graphics = false;
              };

              #services.getty.autologinUser = "root";
              services.qemuGuest.enable = true;
              services.openssh.enable = true;
              services.openssh.permitRootLogin = "yes";

              networking.hostName = "ttapi";
              networking.firewall.allowedTCPPorts = [ 5432 22 ];

              users.extraUsers.root.password = "";
              users.mutableUsers = false;

              environment.systemPackages = with pkgs; [ lsof ];
            }
          )
        ];
      };
    };
}
