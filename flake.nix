{
  description = "Tracking The Trackers - API to submit APKs for testing.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix-src.url = "github:DavHau/mach-nix";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix-src }:
    let
      lib = nixpkgs.lib;
      defaultSystems = flake-utils.lib.defaultSystems;
      buildSystems = lib.lists.subtractLists
        [ "aarch64-darwin" "x86_64-darwin" ] defaultSystems;

      #buildSystems = lib.lists.remove "aarch64-darwin"
      #  (lib.lists.remove "x86_64-darwin" defaultSystems);
    in
      flake-utils.lib.eachSystem buildSystems (
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
                # some extra packages are needed for tests to pass, but
                # absent from requirements.txt:
                requirements = requirements + ''
                  requests
                  pytest-asyncio
                  pytest-tornasync
                  pytest-trio
                '';
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
                          Initialize and enable the Tracking the Trackers API database.
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
          # First build the VM:
          #  $ nixos-rebuild build-vm --flake .#test-vm
          # Then remove old images if any, set port forwards and run VM:
          #  $ rm ttapi-db.qcow2; env QEMU_NET_OPTS=hostfwd=tcp:2221-:22,hostfwd=tcp::5433-:5432 result/bin/run-ttapi-db-vm
          system = "x86_64-linux";
          modules = [
            (
              { modulesPath, ... }: {
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

                services = {
                  getty.autologinUser = "root";
                  openssh.enable = true;
                  openssh.permitRootLogin = "yes";
                };

                networking = {
                  hostName = "ttapi-db";
                  firewall.allowedTCPPorts = [ 5432 22 ];
                };

                users = {
                  extraUsers.root.password = "";
                  mutableUsers = false;
                };
              }
            )
          ];
        };
      };
}
