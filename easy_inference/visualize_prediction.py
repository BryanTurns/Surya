#!/usr/bin/env python3
"""Visualize Surya easy inference predictions from prediction.nc."""

from __future__ import annotations

import argparse
import math
import os
import tempfile
from pathlib import Path

# SunPy and Matplotlib initialize writable cache/config directories at import time.
_CACHE_ROOT = Path(tempfile.gettempdir()) / "surya_visualize_prediction_cache"
_MPLCONFIGDIR = _CACHE_ROOT / "matplotlib"
_SUNPY_CONFIGDIR = _CACHE_ROOT / "sunpy"
_MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
_SUNPY_CONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLCONFIGDIR))
os.environ.setdefault("SUNPY_CONFIGDIR", str(_SUNPY_CONFIGDIR))

import h5netcdf
import matplotlib.pyplot as plt
import numpy as np
import sunpy.visualization.colormaps as sunpy_cm


DEFAULT_INPUT_CANDIDATES = (
    Path("easy_inference/outputs_24h/predictions.nc"),
    Path("easy_inference/outputs_24h/prediction.nc"),
)
DEFAULT_CHANNEL = "aia94"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Surya validation-style visualization from an easy inference "
            "prediction NetCDF file."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=(
            "Path to prediction NetCDF. Defaults to "
            "easy_inference/outputs_24h/predictions.nc when present, otherwise "
            "easy_inference/outputs_24h/prediction.nc."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Path for the PNG output. Defaults to "
            "<input directory>/surya_easy_inference_visualization.png."
        ),
    )
    parser.add_argument(
        "--channel",
        default=DEFAULT_CHANNEL,
        help=f"Channel to visualize. Defaults to {DEFAULT_CHANNEL}.",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Sample index in the NetCDF file. Defaults to 0.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum number of prediction steps to plot. Defaults to all steps.",
    )
    parser.add_argument(
        "--max-pixels-per-side",
        type=int,
        default=1024,
        help=(
            "Downsample displayed frames to at most this many pixels per side. "
            "Use 0 to render full-resolution frames."
        ),
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=120,
        help="PNG output DPI. Defaults to 120.",
    )
    return parser.parse_args()


def resolve_input_path(input_path: Path | None) -> Path:
    if input_path is not None:
        if not input_path.exists():
            raise FileNotFoundError(f"Input NetCDF file does not exist: {input_path}")
        return input_path

    for candidate in DEFAULT_INPUT_CANDIDATES:
        if candidate.exists():
            return candidate

    candidates_text = ", ".join(str(path) for path in DEFAULT_INPUT_CANDIDATES)
    raise FileNotFoundError(
        f"No default prediction NetCDF found. Tried: {candidates_text}"
    )


def decode_fixed_width_strings(chars: np.ndarray) -> list[str]:
    arr = np.asarray(chars)
    if arr.ndim == 1:
        arr = arr[None, :]

    strings = []
    for row in arr:
        byte_values = []
        for value in row:
            if isinstance(value, (bytes, np.bytes_)):
                byte_values.append(bytes(value))
            else:
                byte_values.append(bytes([int(value)]))
        strings.append(b"".join(byte_values).decode("utf-8").rstrip("\x00 ").strip())
    return strings


def display_frame(frame: np.ndarray, max_pixels_per_side: int) -> np.ndarray:
    frame = np.asarray(frame, dtype=np.float32)
    if max_pixels_per_side <= 0:
        return frame

    stride = max(1, math.ceil(max(frame.shape) / max_pixels_per_side))
    return frame[::stride, ::stride]


def channel_cmap(channel: str):
    cmap_name = f"sdo{channel}"
    return sunpy_cm.cmlist.get(cmap_name, "gray")


def finite_min_and_q99(frame: np.ndarray) -> tuple[float, float] | None:
    finite = frame[np.isfinite(frame)]
    if finite.size == 0:
        return None
    return float(np.min(finite)), float(np.quantile(finite, 0.99))


def load_plot_frames(
    nc: h5netcdf.File,
    sample_idx: int,
    channel: str,
    steps: int,
    max_pixels_per_side: int,
) -> tuple[list[np.ndarray], list[np.ndarray], float, float]:
    prediction_var = nc.variables[channel]
    ground_truth_var = nc.variables[f"gt_{channel}"]

    predictions = []
    ground_truth = []
    vmin = float("-inf")
    vmax = float("inf")

    for step_idx in range(steps):
        gt_frame = np.asarray(
            ground_truth_var[sample_idx, step_idx, :, :], dtype=np.float32
        )
        pred_frame = np.asarray(
            prediction_var[sample_idx, step_idx, :, :], dtype=np.float32
        )

        for frame in (gt_frame, pred_frame):
            frame_stats = finite_min_and_q99(frame)
            if frame_stats is None:
                continue
            frame_min, frame_q99 = frame_stats
            vmin = max(vmin, frame_min)
            vmax = min(vmax, frame_q99)

        ground_truth.append(display_frame(gt_frame, max_pixels_per_side))
        predictions.append(display_frame(pred_frame, max_pixels_per_side))

    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        finite_frames = [
            frame[np.isfinite(frame)].ravel()
            for frame in ground_truth + predictions
            if np.isfinite(frame).any()
        ]
        if not finite_frames:
            raise ValueError("No finite values found in selected frames.")
        combined = np.concatenate(finite_frames)
        vmin = float(np.min(combined))
        vmax = float(np.quantile(combined, 0.99))

    return ground_truth, predictions, vmin, vmax


def visualize_prediction(
    input_path: Path | str | None = None,
    output_path: Path | str | None = None,
    channel: str = DEFAULT_CHANNEL,
    sample: int = 0,
    max_steps: int | None = None,
    max_pixels_per_side: int = 1024,
    dpi: int = 120,
) -> Path:
    input_path = resolve_input_path(None if input_path is None else Path(input_path))
    output_path = Path(output_path) if output_path is not None else input_path.with_name(
        "surya_easy_inference_visualization.png"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with h5netcdf.File(input_path, "r") as nc:
        if channel not in nc.variables:
            raise KeyError(
                f"Channel variable not found in {input_path}: {channel}"
            )
        if f"gt_{channel}" not in nc.variables:
            raise KeyError(
                f"Ground-truth variable not found in {input_path}: gt_{channel}"
            )

        sample_count = nc.dimensions["sample"].size
        prediction_steps = nc.dimensions["prediction_time"].size
        if sample < 0 or sample >= sample_count:
            raise IndexError(
                f"Sample index {sample} is outside 0..{sample_count - 1}"
            )

        steps = (
            prediction_steps
            if max_steps is None
            else min(max_steps, prediction_steps)
        )
        if steps <= 0:
            raise ValueError("max_steps must be positive when provided.")

        prediction_timestamps = decode_fixed_width_strings(
            nc.variables["prediction_timestamps"][sample, :steps, :]
        )
        input_timestamps = decode_fixed_width_strings(
            nc.variables["input_timestamps"][sample, :, :]
        )
        ground_truth, predictions, vmin, vmax = load_plot_frames(
            nc=nc,
            sample_idx=sample,
            channel=channel,
            steps=steps,
            max_pixels_per_side=max_pixels_per_side,
        )

    plt_kwargs = {
        "vmin": vmin,
        "vmax": vmax,
        "cmap": channel_cmap(channel),
        "origin": "lower",
    }
    fig, ax = plt.subplots(steps, 2, figsize=(10, 4 * steps), squeeze=False)

    for step_idx in range(steps):
        timestamp = prediction_timestamps[step_idx]

        ax[step_idx, 0].axis("off")
        ax[step_idx, 0].imshow(ground_truth[step_idx], **plt_kwargs)
        ax[step_idx, 0].set_title(f"Ground Truth - {timestamp}")

        ax[step_idx, 1].axis("off")
        ax[step_idx, 1].imshow(predictions[step_idx], **plt_kwargs)
        ax[step_idx, 1].set_title(f"Prediction - {timestamp}")

    fig.suptitle(
        f"Surya Easy Inference - {channel.upper()}\n"
        f"Inputs: {', '.join(input_timestamps)}",
        y=0.995,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    output_path = visualize_prediction(
        input_path=args.input,
        output_path=args.output,
        channel=args.channel,
        sample=args.sample,
        max_steps=args.max_steps,
        max_pixels_per_side=args.max_pixels_per_side,
        dpi=args.dpi,
    )

    print(f"Saved visualization at {output_path}")


if __name__ == "__main__":
    main()
