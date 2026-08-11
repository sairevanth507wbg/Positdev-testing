"""Shiny for Python demo app, packaged for Posit Connect git-backed publishing.

The dataset is generated from a fixed seed rather than read from disk, so a
freshly deployed copy shows byte-identical numbers to the local one -- which is
what makes this useful as a deployment smoke test.
"""

from __future__ import annotations

import platform
import socket
import sys
from importlib.metadata import PackageNotFoundError, version

import numpy as np
import pandas as pd
from shiny import App, reactive, render, ui

APP_VERSION = "1.1.0"

REGIONS = ["North", "South", "East", "West"]
CHANNELS = ["Online", "Retail", "Partner"]
SEED = 20260811


def build_sales() -> pd.DataFrame:
    """Deterministic synthetic order book."""
    rng = np.random.default_rng(SEED)
    n = 1500
    start = pd.Timestamp("2025-01-01")

    df = pd.DataFrame(
        {
            "order_date": start + pd.to_timedelta(rng.integers(0, 365, n), unit="D"),
            "region": rng.choice(REGIONS, n),
            "channel": rng.choice(CHANNELS, n, p=[0.50, 0.30, 0.20]),
            "units": rng.integers(1, 25, n),
            "unit_price": rng.uniform(12.0, 240.0, n).round(2),
        }
    )
    df["revenue"] = (df["units"] * df["unit_price"]).round(2)
    return df.sort_values("order_date", ignore_index=True)


SALES = build_sales()
MIN_DATE = SALES["order_date"].min().date()
MAX_DATE = SALES["order_date"].max().date()


def pkg_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_date_range(
            "dates",
            "Order date",
            start=MIN_DATE,
            end=MAX_DATE,
            min=MIN_DATE,
            max=MAX_DATE,
        ),
        ui.input_checkbox_group("regions", "Region", choices=REGIONS, selected=REGIONS),
        ui.input_checkbox_group(
            "channels", "Channel", choices=CHANNELS, selected=CHANNELS
        ),
        ui.input_slider(
            "min_revenue", "Minimum order value", min=0, max=6000, value=0, step=250
        ),
        ui.input_action_button("reset", "Reset filters", class_="btn-outline-secondary"),
        ui.download_button("download_orders", "Download CSV", class_="btn-outline-primary"),
        width=280,
        open="desktop",
    ),
    ui.layout_columns(
        ui.value_box("Revenue", ui.output_text("kpi_revenue")),
        ui.value_box("Orders", ui.output_text("kpi_orders")),
        ui.value_box("Average order value", ui.output_text("kpi_aov")),
        fill=False,
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Revenue by region and channel"),
            ui.output_data_frame("summary_table"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Matching orders"),
            ui.output_data_frame("orders_table"),
            full_screen=True,
        ),
        col_widths=[5, 7],
    ),
    ui.card(
        ui.card_header("Runtime"),
        ui.output_ui("runtime_info"),
    ),
    title=f"Positdev sales explorer v{APP_VERSION}",
    fillable=False,
)


def server(input, output, session):
    @reactive.calc
    def filtered() -> pd.DataFrame:
        start, end = input.dates()
        df = SALES
        mask = (
            df["order_date"].between(pd.Timestamp(start), pd.Timestamp(end))
            & df["region"].isin(input.regions())
            & df["channel"].isin(input.channels())
            & (df["revenue"] >= input.min_revenue())
        )
        return df.loc[mask]

    @reactive.effect
    @reactive.event(input.reset)
    def _reset_filters():
        ui.update_date_range("dates", start=MIN_DATE, end=MAX_DATE)
        ui.update_checkbox_group("regions", selected=REGIONS)
        ui.update_checkbox_group("channels", selected=CHANNELS)
        ui.update_slider("min_revenue", value=0)

    @render.text
    def kpi_revenue():
        return f"${filtered()['revenue'].sum():,.0f}"

    @render.text
    def kpi_orders():
        return f"{len(filtered()):,}"

    @render.text
    def kpi_aov():
        df = filtered()
        if df.empty:
            return "--"
        return f"${df['revenue'].mean():,.0f}"

    @render.data_frame
    def summary_table():
        df = filtered()
        if df.empty:
            return render.DataGrid(pd.DataFrame({"Region": [], "Channel": []}))

        out = (
            df.groupby(["region", "channel"], as_index=False)
            .agg(orders=("revenue", "size"), revenue=("revenue", "sum"))
            .sort_values("revenue", ascending=False, ignore_index=True)
        )
        out["revenue"] = out["revenue"].map(lambda v: f"${v:,.0f}")
        out.columns = ["Region", "Channel", "Orders", "Revenue"]
        return render.DataGrid(out, width="100%")

    @render.data_frame
    def orders_table():
        out = filtered().copy()
        out["order_date"] = out["order_date"].dt.strftime("%Y-%m-%d")
        out["unit_price"] = out["unit_price"].map(lambda v: f"${v:,.2f}")
        out["revenue"] = out["revenue"].map(lambda v: f"${v:,.2f}")
        out.columns = ["Date", "Region", "Channel", "Units", "Unit price", "Revenue"]
        return render.DataGrid(out, width="100%", height="360px")

    @render.download(filename="filtered_orders.csv")
    def download_orders():
        yield filtered().to_csv(index=False)

    @render.ui
    def runtime_info():
        rows = [
            ("App version", APP_VERSION),
            ("Python", sys.version.split()[0]),
            ("Platform", platform.platform()),
            ("Host", socket.gethostname()),
            ("shiny", pkg_version("shiny")),
            ("pandas", pkg_version("pandas")),
            ("numpy", pkg_version("numpy")),
            ("Rows loaded", f"{len(SALES):,}"),
        ]
        return ui.tags.dl(
            *[
                item
                for label, value in rows
                for item in (
                    ui.tags.dt(label, class_="text-muted fw-normal"),
                    ui.tags.dd(value, class_="font-monospace"),
                )
            ],
            class_="row row-cols-2 mb-0 small",
        )


app = App(app_ui, server)
