"""Show a fixed illustrative known-form fit without a benchmark or PySR search."""

import argparse
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ringdown_sr.losses import mean_squared_error
from ringdown_sr.noise import gaussian_white_noise
from ringdown_sr.reference_fit import fit_ringdown
from ringdown_sr.signals import ringdown_signal, sample_times


def main() -> None:
    """Print fitted parameters and save a plot using a noninteractive backend."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(tempfile.gettempdir()) / "ringdown-reference-fit.png",
    )
    args = parser.parse_args()
    plt.switch_backend("Agg")
    time = sample_times(128, 4096.0)
    truth = {
        "amplitude": 1.0,
        "frequency_hz": 250.0,
        "decay_time_s": 0.008,
        "phase_rad": 0.0,
    }
    signal = ringdown_signal(time, **truth)
    sigma = 0.1
    noise = gaussian_white_noise(
        len(time),
        standard_deviation=sigma,
        rng=np.random.Generator(np.random.PCG64(42)),
    )
    observed = signal + noise
    # Bounds and starts are illustrative, fixed independently of the truth dictionary.
    fit = fit_ringdown(
        time,
        observed,
        frequency_bounds_hz=(100.0, 500.0),
        decay_time_bounds_s=(0.002, 0.03),
        initial_points=[(150.0, 0.004), (300.0, 0.015), (450.0, 0.004)],
        covariance=sigma**2 * np.eye(len(time)),
    )

    print("Klassischer Referenzfit mit bekanntem Formansatz (Demonstration)")
    print(f"{'Parameter':<22} {'Vorgegeben':>14} {'Geschätzt':>14}")
    for name, label in [
        ("amplitude", "Amplitude"),
        ("frequency_hz", "Frequenz (Hz)"),
        ("decay_time_s", "Abklingzeit (s)"),
        ("phase_rad", "Phase (rad)"),
    ]:
        print(f"{label:<22} {truth[name]:14.8g} {getattr(fit, name):14.8g}")
    print(f"MSE an Messdaten: {fit.ordinary_mse:.8g}")
    print(f"Kovarianzgewichteter Wert Q/N: {fit.covariance_mean_squared:.8g}")
    print(
        f"MSE zur bekannten Testkurve: {mean_squared_error(fit.prediction - signal):.8g}"
    )
    print(
        f"Gewählter Start: {fit.selected_start_index + 1}; aktive Grenzen (f, tau): {fit.active_mask}"
    )
    print(
        f"Numerischer Rang der reduzierten Jacobi-Matrix: {fit.nonlinear_jacobian_rank}/2"
    )
    for index, attempt in enumerate(fit.attempts, start=1):
        print(
            f"Start {index}: konvergiert={attempt.converged}, verwendbar={attempt.usable}, "
            f"Status={attempt.status}, nfev={attempt.nfev}"
        )

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True, layout="constrained")
    milliseconds = time * 1000
    axes[0].scatter(
        milliseconds,
        observed,
        color="gray",
        s=14,
        alpha=0.6,
        label="Verrauschte Messdaten",
    )
    axes[0].plot(milliseconds, signal, label="Bekanntes Signal", linewidth=2)
    axes[0].plot(
        milliseconds, fit.prediction, "--", label="Klassischer Fit", linewidth=2
    )
    axes[0].set_title("Klassischer Referenzfit – bekannter Formansatz")
    axes[0].set_ylabel("Amplitude (normiert)")
    axes[1].plot(
        milliseconds, fit.residual, color="darkorange", label="Messdaten − Fit"
    )
    axes[1].axhline(0, color="gray", linewidth=0.7)
    axes[1].set_xlabel("Zeit (ms)")
    axes[1].set_ylabel("Residuum")
    for axis in axes:
        axis.legend()
        axis.grid(alpha=0.2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)
    print(f"Diagramm: {args.output.resolve()}")
    print(
        "Einzelner Demofall; eine wissenschaftliche Bewertung und PySR-Suche stehen noch aus."
    )


if __name__ == "__main__":
    main()
