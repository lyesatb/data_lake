"""Point d'entree en ligne de commande de la plateforme UrbanHub.

Exemples :
    python -m urbanhub.cli init
    python -m urbanhub.cli batch  --years 5 --max-stations 20
    python -m urbanhub.cli stream --iterations 3 --interval 60
    python -m urbanhub.cli iot    --iterations 5 --interval 5 --simulate
    python -m urbanhub.cli process
    python -m urbanhub.cli analyze
    python -m urbanhub.cli pipeline --demo   # chaine complete de demonstration
"""
from __future__ import annotations

import argparse

from urbanhub import config
from urbanhub.utils.logging_utils import get_logger

log = get_logger("cli")


def cmd_init(_args) -> None:
    config.ensure_dirs()
    log.info("Data lake initialise sous : %s", config.DATA_DIR)


def cmd_batch(args) -> None:
    from urbanhub.ingestion import batch_weather
    config.ensure_dirs()
    batch_weather.download_weather(
        years_back=args.years,
        max_stations=args.max_stations,
        max_workers=args.workers,
    )


def cmd_stream(args) -> None:
    from urbanhub.ingestion import streaming_citybikes
    config.ensure_dirs()
    streaming_citybikes.stream(
        iterations=args.iterations,
        duration_sec=args.duration,
        interval_sec=args.interval,
    )


def cmd_iot(args) -> None:
    from urbanhub.ingestion import iot_openaq
    config.ensure_dirs()
    if args.backfill_hours:
        iot_openaq.backfill(hours=args.backfill_hours, seed=args.seed)
        return
    simulate = True if args.simulate else (False if args.real else None)
    iot_openaq.stream(
        iterations=args.iterations,
        duration_sec=args.duration,
        interval_sec=args.interval,
        simulate=simulate,
        seed=args.seed,
    )


def cmd_process(args) -> None:
    from urbanhub.processing import weather, citybikes, openaq
    config.ensure_dirs()
    weather.process_weather(max_files=args.max_files)
    citybikes.process_citybikes()
    df = openaq.process_openaq()
    if not df.empty:
        openaq.pivot_city_hour(df)


def cmd_analyze(_args) -> None:
    from urbanhub.analysis import (weather_analysis, mobility_analysis,
                                   pollution_analysis, cross_analysis)
    config.ensure_dirs()
    weather_analysis.run()
    mobility_analysis.run()
    pollution_analysis.run()
    cross_analysis.run()
    log.info("Indicateurs ecrits sous : %s", config.INDICATORS_DIR)


def cmd_dashboard(args) -> None:
    """Lance le tableau de bord interactif Streamlit."""
    import subprocess
    import sys
    from pathlib import Path

    app = Path(__file__).resolve().parent / "dashboard" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app),
           "--server.port", str(args.port)]
    log.info("Lancement du tableau de bord : http://localhost:%s", args.port)
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        log.error("Streamlit n'est pas installe. Faites : pip install streamlit")
    except KeyboardInterrupt:
        log.info("Tableau de bord arrete.")


def cmd_pipeline(args) -> None:
    """Chaine complete : ingestion -> stockage -> traitement -> analyse."""
    config.ensure_dirs()

    # 1. Flux batch (limite en mode demo pour un run rapide)
    from urbanhub.ingestion import batch_weather, streaming_citybikes, iot_openaq
    max_stations = 8 if args.demo else None
    years = 2 if args.demo else config.NOAA.years_back
    batch_weather.download_weather(years_back=years, max_stations=max_stations)

    # 2. Flux streaming velos
    streaming_citybikes.stream(iterations=args.stream_iters, interval_sec=args.interval)

    # 3. Flux IoT pollution : historique simule (profils diurnes) + collecte live
    if args.iot_backfill:
        iot_openaq.backfill(hours=args.iot_backfill, seed=args.seed)
    iot_openaq.stream(iterations=args.iot_iters, interval_sec=args.interval,
                      simulate=None, seed=args.seed)

    # 4. Traitement
    cmd_process(args)

    # 5. Analyse
    cmd_analyze(args)
    log.info("Pipeline UrbanHub termine.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="urbanhub", description="Plateforme Smart City UrbanHub")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialise le data lake").set_defaults(func=cmd_init)

    b = sub.add_parser("batch", help="Ingestion batch meteo NOAA (France)")
    b.add_argument("--years", type=int, default=config.NOAA.years_back)
    b.add_argument("--max-stations", type=int, default=None)
    b.add_argument("--workers", type=int, default=config.NOAA.max_workers)
    b.set_defaults(func=cmd_batch)

    s = sub.add_parser("stream", help="Ingestion streaming velos CityBikes")
    s.add_argument("--iterations", type=int, default=1)
    s.add_argument("--duration", type=int, default=None)
    s.add_argument("--interval", type=int, default=config.CITYBIKES.poll_interval_sec)
    s.set_defaults(func=cmd_stream)

    i = sub.add_parser("iot", help="Ingestion IoT pollution OpenAQ")
    i.add_argument("--iterations", type=int, default=1)
    i.add_argument("--duration", type=int, default=None)
    i.add_argument("--interval", type=int, default=config.OPENAQ.poll_interval_sec)
    i.add_argument("--simulate", action="store_true", help="Force le mode simule")
    i.add_argument("--real", action="store_true", help="Force l'appel reel a OpenAQ")
    i.add_argument("--backfill-hours", type=int, default=None,
                   help="Genere un historique IoT simule sur N heures (profils diurnes)")
    i.add_argument("--seed", type=int, default=42)
    i.set_defaults(func=cmd_iot)

    pr = sub.add_parser("process", help="Nettoyage / normalisation des trois flux")
    pr.add_argument("--max-files", type=int, default=None)
    pr.set_defaults(func=cmd_process)

    sub.add_parser("analyze", help="Analyse + indicateurs urbains").set_defaults(func=cmd_analyze)

    db = sub.add_parser("dashboard", help="Lance le tableau de bord Streamlit")
    db.add_argument("--port", type=int, default=8501)
    db.set_defaults(func=cmd_dashboard)

    pl = sub.add_parser("pipeline", help="Chaine complete de demonstration")
    pl.add_argument("--demo", action="store_true", help="Mode demo (perimetre reduit)")
    pl.add_argument("--stream-iters", type=int, default=2)
    pl.add_argument("--iot-iters", type=int, default=6)
    pl.add_argument("--iot-backfill", type=int, default=72,
                    help="Heures d'historique IoT simule a generer (0 pour desactiver)")
    pl.add_argument("--interval", type=int, default=5)
    pl.add_argument("--max-files", type=int, default=None)
    pl.add_argument("--seed", type=int, default=42)
    pl.set_defaults(func=cmd_pipeline)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
