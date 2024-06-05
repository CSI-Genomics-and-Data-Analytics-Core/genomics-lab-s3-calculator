import faicons as fa
import numpy as np
import plotly.express as px
from scipy.stats import truncnorm
import pandas as pd

# Load data and compute static values
from shared import app_dir
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly


# Add main content
ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "ellipsis": fa.icon_svg("ellipsis"),
    "file": fa.icon_svg("folder-open"),
    "transfer": fa.icon_svg("right-left"),
}

# Default values
mode="Simple"
currency = "USD"
storage_class="Standard Storage"
total_months = 1

kb_in_gb = 1048576
gb_in_tb = 1024

# AWS pricing information
# https://aws.amazon.com/s3/pricing/
# always consider the highest tier, ideally cost reduces as storage increases
# pricing is in USD
standard_storage_cost_gb = 0.025 
put_post_copy_list_request_cost = 0.000005
get_select_request_cost = 0.0000004
deep_archive_storage_cost_gb = 0.0099
deep_archive_retrieval_cost_gb = 0.02
deep_archive_request_cost = 0.0000025

# Add page title and sidebar
ui.HTML("<em><span>Calculations made based on the pricing information retrieved from AWS (Singapore) as of June 05, 2024.</span></em>")
ui.page_opts(title=ui.HTML("<span style='font-size: 30px; color: #5C6490;'> S3 Cost Study<span>"), fillable=True, window_title="GeDaC S3 Cost Study", lang="en")

with ui.sidebar(open="desktop", width=500, fill=True):

    ui.input_radio_buttons(
        "mode",
        "Calculation Mode",
                {
            "Simple": ui.span("Simple", style="color: #00AA00;"),
            "Advanced": ui.span("Advanced", style="color: #FF0000;"),
        },
        selected=mode,
        inline=True,
    )

    ui.HTML("<hr>")

    with ui.panel_conditional("input.mode === 'Simple'"):
        ui.input_radio_buttons(
            "s_class",
            "Storage Class",
                    {
                "Standard Storage": ui.span("Standard Storage"),
                "Deep Archive": ui.span("Deep Archive"),
            },
            selected=storage_class,
            inline=True,
        )

        ui.input_numeric("s_samples", "No of Samples/Files:", 0, min=1, max=100000),

        ui.input_numeric("s_size", "Total Storage Size (TB):", 0, min=1, max=1000),

        ui.input_slider(
            "s_duration",
            "Storage Duration (Months)",
            0,
            max=120,
            value=total_months,
            post=" ",
            animate= False,
            step=1,
            drag_range=False,
        )

        ui.input_numeric("s_download", "Download Size per year (TB):", 0, min=0, max=1000)

        ui.input_numeric("s_download_times", "Download Times (per year):", 0, min=0, max=100, step=1)

        ui.input_numeric("s_download_samples", "No of Downloading Samples/Files:", 0, min=1, max=100000),

    with ui.panel_conditional("input.mode === 'Advanced'"):

        ui.input_slider(
            "a_duration",
            "Timeline (years)",
            0,
            max=total_months,
            value=total_months,
            post=" ",
            animate= False,
            step=1,
            drag_range=False,
            
        )

        ui.input_radio_buttons(
            "a_class",
            "Storage Class",
                    {
                "Standard Storage": ui.span("Standard Storage"),
                "Deep Archive": ui.span("Deep Archive"),
            },
            selected=["Standard Storage"],
            inline=False,
        )

    ui.input_action_button("reset", "Reset filter")

with ui.layout_columns(fill=False):
   ui.input_select(
        "currency",
        "Currency:",
        choices={
            "USD" :"US Dollar",
            "SGD" : "Singapore Dollar",
        },
        selected=currency,
    )

with ui.layout_columns(fill=False):
    with ui.value_box(showcase=ICONS["currency-dollar"]):
        ui.HTML("<strong>Total Cost</strong>")

        @render.express
        def total_amount():
            amount=calculate_info()["total_cost"]
            if input.currency() == "SGD":
                amount = amount*1.35
            f"{amount:.2f} {input.currency()}"

    with ui.value_box(showcase=ICONS["file"]):
        ui.HTML("<strong>Storage Cost</strong>")

        @render.express
        def total_storage():
            amount=calculate_info()["storage_cost"]
            if input.currency() == "SGD":
                amount = amount*1.35
            f"{amount:.2f} {input.currency()}"

    with ui.value_box(showcase=ICONS["transfer"]):
        ui.HTML("<strong>Data-Transfer Cost</strong>")

        @render.express
        def total_download():
            amount=calculate_info()["download_cost"]
            if input.currency() == "SGD":
                amount = amount*1.35
            f"{amount:.2f} {input.currency()}"


with ui.layout_columns(col_widths=[12]):
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Accumulated Cost"
            with ui.popover(title="Add a color variable"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "tip_perc_y",
                    "Split by:",
                    ["sex", "smoker", "day", "time"],
                    selected="day",
                    inline=True,
                )

        # @render_plotly
        # def tip_perc():
            # from ridgeplot import ridgeplot

            # dat = calculateInfo()
            # dat["percent"] = dat.tip / dat.total_bill
            # yvar = input.tip_perc_y()
            # uvals = dat[yvar].unique()

            # samples = [[dat.percent[dat[yvar] == val]] for val in uvals]

            # plt = ridgeplot(
            #     samples=samples,
            #     labels=uvals,
            #     bandwidth=0.01,
            #     colorscale="viridis",
            #     colormode="row-index",
            # )

            # plt.update_layout(
            #     legend=dict(
            #         orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
            #     )
            # )

            # return plt

ui.include_css(app_dir / "styles.css")

# --------------------------------------------------------
# Reactive calculations and effects
# --------------------------------------------------------
@reactive.calc
def calculate_info():
    storage = input.s_class() if input.s_class() else "Standard Storage"
    storage_size = input.s_size() if input.s_size() else 0
    sample_count = input.s_samples() if input.s_samples() else 0
    download_size = input.s_download() if input.s_download() else 0
    download_times = input.s_download_times() if input.s_download_times() else 0
    download_count = input.s_download_samples() if input.s_download_samples() else 0
    months = input.s_duration() if input.s_duration() else 0

    if input.mode() == "Simple":
        return calculate_simple(storage, storage_size, sample_count, download_size, download_times, download_count, months)
    else:
        return calculate_advanced(storage, storage_size, sample_count, download_size, download_times, download_count, months)


def calculate_simple(storage, storage_size, sample_count, download_size, download_times, download_count, months):
    storage_cost = calculate_storage_cost(storage, storage_size*gb_in_tb, months, n_samples=sample_count, requests_per_obj=1)
    download_cost = calculate_data_transfer_cost(download_size*gb_in_tb, download_count, requests_per_obj=2) * download_times
    total_cost = storage_cost + download_cost
    return {'total_cost': total_cost, 'storage_cost': storage_cost, 'download_cost': download_cost}

def calculate_advanced(storage, storage_size, sample_count, download_size, download_times, download_count, months):
    storage_cost = calculate_storage_cost(storage, storage_size*gb_in_tb, months, n_samples=sample_count, requests_per_obj=1)
    download_cost = calculate_data_transfer_cost(download_size*gb_in_tb, download_count, requests_per_obj=2) * download_times
    total_cost = storage_cost + download_cost
    return {'total_cost': total_cost, 'storage_cost': storage_cost, 'download_cost': download_cost}



def calculate_storage_cost(storage, gb, months, n_samples, requests_per_obj=1):
    storage_cost_gb = 0.002
    storage_overhead_kb = 8

    # Metadata overhead
    metadata_overhead_kb = 32
    metadata_overhead_cost_per_gb = 0.002

    if storage == "Standard Storage":
        storage_cost_gb = standard_storage_cost_gb
        storage_overhead_kb = 0
        metadata_overhead_kb = 0
    else:
        storage_cost_gb = deep_archive_storage_cost_gb

    overhead_total_gb = (metadata_overhead_kb /kb_in_gb) * n_samples
    metadata_cost_overhead = metadata_overhead_cost_per_gb * overhead_total_gb

    # Storage overhead
    storage_cost_overhead = (storage_overhead_kb / kb_in_gb) * n_samples # this is tiered

    storage_cost = storage_cost_gb * gb

    # Cost per request
    requests_cost = requests_per_obj * n_samples * put_post_copy_list_request_cost

    monthly_cost = metadata_cost_overhead + storage_cost_overhead + requests_cost + storage_cost
    total_cost = monthly_cost * months
    return total_cost if total_cost and total_cost > 0 else 0

def calculate_data_retrival_cost(gb, n_samples, requests_per_obj=2):
    # Data Retrieval Cost = Data Retrieved (GB) x $0.0200 per GB + $0.0025 per 1,000 requests
    gb_cost = gb * deep_archive_retrieval_cost_gb
    requests_cost = n_samples * deep_archive_request_cost
    total_cost = gb_cost + requests_cost
    return total_cost if total_cost and total_cost > 0 else 0

def calculate_data_transfer_cost(gb, n_samples, requests_per_obj=2):
    # Data Transfer OUT to Internet: Cost = Data Transferred (GB) x $0.09 per GB
    # Data Transfer IN from Internet: No charge
    # GET and all other Requests: $0.0004 per 1,000 requests
    requests_cost = requests_per_obj * n_samples * get_select_request_cost
    transfer_cost = gb * standard_storage_cost_gb
    total_cost = requests_cost + transfer_cost
    return total_cost if total_cost and total_cost > 0 else 0

def accumulate_costs(accumulated_storage):
    accumulated_storage["Cost USD"].sum()
    cost_per_year = accumulated_storage.groupby("Year").sum()
    px.bar(cost_per_year.reset_index(), x="Year", y="Cost USD", title="Cost of storage")


@reactive.effect
@reactive.event(input.reset)
def _():
    ui.update_numeric("s_samples", value=0)
    ui.update_numeric("s_size", value=0)
    ui.update_numeric("s_download", value=0)
    ui.update_numeric("s_download_times", value=0)
    ui.update_numeric("s_download_samples", value=0)
    ui.update_slider("a_duration", value=total_months)
    ui.update_checkbox_group("a_class", selected=storage_class)
    ui.update_select("currency", selected=currency)
    ui.update_radio_buttons("mode", selected=mode)