def main() -> None:
    """Start the installed command without importing Julia or PySR."""
    from ringdown_sr.cli import main as cli_main

    raise SystemExit(cli_main())
