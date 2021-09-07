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
                # requests is absent from 'requirements.txt', but must be installed
                # for starlette TestClient tests to run.
                requirements = requirements + "requests";
              };
            }
      ) // {
      nixosModules = {
        ttapi-db = (
          { config, lib, pkgs, ... }:
            let
              db_user = "bincache";
              db_name = "bincache";
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
                    enableTCPIP = true;
                    # Make sure we can auth from outside of vm..
                    authentication = lib.mkForce ''
                      local  all  all                         trust
                      host   all  ${db_user}  10.0.0.0/8      trust
                      host   all  ${db_user}  172.16.0.0/12   trust
                      host   all  ${db_user}  192.168.0.0/16  trust
                    '';
                    ensureDatabases = [ "${db_name}" ];
                    ensureUsers = [
                      {
                        name = "${db_user}";
                        ensurePermissions = {
                          "DATABASE ${db_name}" = "ALL PRIVILEGES";
                          "ALL TABLES IN SCHEMA public" = "ALL PRIVILEGES";
                        };
                      }
                    ];
                    # Initialize table and indexes from project's db.sql
                    initialScript = pkgs.writeTextFile {
                      name = "initialScript.sql";
                      text = (builtins.readFile ./db/db.sql); #+ ''
                    };
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
          self.nixosModules.ttapi-db
          (
            { config, lib, pkgs, ... }: {
              system.configurationRevision = self.rev or "dirty";
              virtualisation = {
                graphics = false;
              };

              services.getty.autologinUser = "root";
              services.openssh.enable = true;
              services.openssh.permitRootLogin = "yes";

              networking.hostName = "ttapi-db";
              networking.firewall.allowedTCPPorts = [ 5432 22 ];

              users.extraUsers.root.password = "";
              users.mutableUsers = false;
            }
          )
        ];
      };
    };
}
