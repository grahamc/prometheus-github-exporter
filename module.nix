{ config, pkgs, ... }:
{
  systemd.services.prometheus-github-project-exporter = {
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" ];
    serviceConfig = {
      Restart = "always";
      RestartSec = "60s";
      PrivateTmp =  true;
    };

    path = [
      (pkgs.python3.withPackages (p: [ p.prometheus_client p.requests ]))
    ];

    script = "exec python3 ${./scrape.py} ${./config.py}";
  };
}
