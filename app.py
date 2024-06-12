import faicons as fa
import numpy as np
import plotly.express as px
from scipy.stats import truncnorm
import pandas as pd

# Load data and compute static values
from shared import app_dir, ngs_details
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly
import pandas as pd
from htmltools import TagList, div


ngs_df = reactive.value(ngs_details)

# Add main content
ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "ellipsis": fa.icon_svg("ellipsis"),
    "file": fa.icon_svg("folder-open"),
    "dna": fa.icon_svg("dna"),
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
data_transfer_out_cost = 0.09
put_post_copy_list_request_cost = 0.000005
get_select_1000_request_cost = 0.0004
get_select_request_cost = 0.0000004
deep_archive_storage_cost_gb = 0.002
deep_archive_retrieval_cost_gb = 0.02
deep_archive_request_cost = 0.0000025

# Add page title and sidebar
ui.HTML("<em><span>Calculations made based on the pricing information retrieved from AWS (Singapore) as of June 05, 2024.</span></em>")
ui.page_opts(title=ui.HTML("<span style='font-size: 40px;'> S3 Cost Study for Labs<span>"), fillable=True, window_title="GeDaC S3 Cost Study", lang="en")

with ui.sidebar(open="desktop", width=500, fill=True):

    ui.input_action_button("sample_info", "Show NGS Size Details", icon=ICONS["dna"])

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

    # add a tooltip
    ui.HTML("<p style='font-size: 12px;'><em>Simple mode is for quick calculations, while Advanced mode allows for more detailed inputs.</em></p>")
   
    ui.input_radio_buttons(
        "s_class",
        "Storage Class",
                {
            "Standard Storage": ui.span("Standard Storage"),
            "Deep Archive": ui.span("Glacier Deep Archive"),
        },
        selected=storage_class,
        inline=True,
    )
    # ui.HTML("<hr>")

    with ui.panel_conditional("input.mode === 'Simple'"):
        with ui.accordion(id="simple_mode", multiple=True, open=True, ):
            with ui.accordion_panel(f"Storage Inputs", icon=ICONS["file"], style="background-color: #F8F8F8;"):
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
                ui.HTML("<br/>")

            with ui.accordion_panel(f"Data-Transfer Inputs", icon=ICONS["transfer"], style="background-color: #F8F8F8;"):
                ui.input_numeric("s_download", "Download Size (TB):", 0, min=0, max=1000),
                ui.input_numeric("s_download_times", "Download Times:", 0, min=0, max=100, step=1),
                ui.input_numeric("s_download_samples", "No of Downloading Samples/Files:", 0, min=1, max=100000),

    with ui.panel_conditional("input.mode === 'Advanced'"):
        ui.input_numeric("a_samples", "No of Samples per Month:", 0, min=1, max=100000),
        ui.input_numeric("a_size", "Average Sample Size:", 0, min=1, max=1000),
        ui.input_slider(
            "a_duration",
            "Storage Duration (Months)",
            0,
            max=120,
            value=total_months,
            post=" ",
            animate= False,
            step=1,
            drag_range=False,
        )
        ui.HTML("<br/>")

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

ui.input_action_button("show", "Show Cost Breakdown")

with ui.layout_columns(col_widths={"sm": (12, 12), "md": (4,8), "lg": (5,7)}, fill=False, height="300px"):
    @render_plotly
    def pie_chart():
        return pie_chart(calculate_info()["storage_cost"], calculate_info()["download_cost"])
    
    @render_plotly
    def bar_chart_distribution():
        storage_cost_distribution = calculate_info()["storage_cost_distribution"]
        return bar_chart_distribution(storage_cost_distribution)   
    
    
with ui.layout_columns(col_widths={12}, fill=False, height="300px"):
    @render_plotly
    def bar_chart_accumulation():
        storage_cost_distribution = calculate_info()["storage_cost_distribution"]
        return bar_chart_accumulation(storage_cost_distribution)    

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
    # create a variable to store array of cost breakdown logs so that we can display it in the UI
    cost_breakdown = []

    # calculate the storage cost
    storage_cost = calculate_storage_cost(storage, storage_size*gb_in_tb, months, n_samples=sample_count, requests_per_obj=1, cost_breakdown=cost_breakdown)
    
    # create a data array for storage cost distribution
    monthly_storage_cost = storage_cost / months if months > 0 else 0
    storage_cost_distribution = [{"Month": i, "Cost": monthly_storage_cost,} for i in range(1, months+1)]

    download_cost = calculate_data_transfer_cost(storage, download_size*gb_in_tb, download_count, download_times, requests_per_obj=2, cost_breakdown=cost_breakdown)
    total_cost = storage_cost + download_cost
    cost_breakdown.append(f"Total Cost: ${storage_cost} + ${download_cost} = ${total_cost}")
    return {'total_cost': total_cost, 'storage_cost': storage_cost, 'download_cost': download_cost, 'cost_breakdown': cost_breakdown, "storage_cost_distribution": storage_cost_distribution}

def calculate_advanced(storage, storage_size, sample_count, download_size, download_times, download_count, months):
    cost_breakdown = []
    storage_cost_distribution = [{"Month": i, "Cost": 1,} for i in range(1, months+1)]

    storage_cost = calculate_storage_cost(storage, storage_size*gb_in_tb, months, n_samples=sample_count, requests_per_obj=1, cost_breakdown=cost_breakdown)
    download_cost = calculate_data_transfer_cost(storage, download_size*gb_in_tb, download_count, download_times, requests_per_obj=2, cost_breakdown=cost_breakdown)
    total_cost = storage_cost + download_cost
    cost_breakdown.append(f"Total Cost: ${storage_cost} + ${download_cost} = ${total_cost}")
    return {'total_cost': total_cost, 'storage_cost': storage_cost, 'download_cost': download_cost, 'cost_breakdown': cost_breakdown, "storage_cost_distribution": storage_cost_distribution}



def calculate_storage_cost(storage, gb, months, n_samples, requests_per_obj=1, cost_breakdown=[]):
    storage_cost_gb = 0.002
    storage_overhead_kb = 8

    # Metadata overhead
    metadata_overhead_kb = 32
    metadata_overhead_cost_per_gb = 0.002
    
    cost_breakdown.append("Storage Cost Breakdown:")

    if storage == "Standard Storage":
        storage_cost_gb = standard_storage_cost_gb
        cost_breakdown.append(f"Standard Storage Cost: ${storage_cost_gb} per GB/Month")
        storage_overhead_kb = 0
        metadata_overhead_kb = 0
    else:
        storage_cost_gb = deep_archive_storage_cost_gb
        cost_breakdown.append(f"Deep Archive Storage Cost: ${storage_cost_gb} per GB/Month")


    overhead_total_gb = (metadata_overhead_kb /kb_in_gb) * n_samples
    metadata_cost_overhead = metadata_overhead_cost_per_gb * overhead_total_gb

    # Storage overhead
    storage_cost_overhead = (storage_overhead_kb / kb_in_gb) * n_samples # this is tiered

    put_post_copy_list_1000_request_cost = put_post_copy_list_request_cost * 1000
    cost_breakdown.append(f"Requests Cost (PUT, POST): ${put_post_copy_list_1000_request_cost} per 1000 requests") 


    monthly_cost = storage_cost_gb * gb
    storage_cost = monthly_cost * months
    cost_breakdown.append(f"Total Storage Cost: ${storage_cost_gb} x {gb} GB x {months} Month(s)= ${storage_cost}")
    
    # Cost per request
    requests_cost = requests_per_obj * n_samples * put_post_copy_list_request_cost

    total_cost = metadata_cost_overhead + storage_cost_overhead + requests_cost + storage_cost
    return total_cost if total_cost and total_cost > 0 else 0

def calculate_data_retrival_cost(gb, n_samples, times, requests_per_obj=2, cost_breakdown=[]):
    cost_breakdown.append("Data Retrieval Cost Breakdown:")
    cost_breakdown.append(f"Data Retrieval Cost: ${deep_archive_retrieval_cost_gb} per GB/Month")
    cost_breakdown.append(f"GET and all other Requests Cost: ${deep_archive_request_cost} per 1000 requests")
    # Data Retrieval Cost = Data Retrieved (GB) x $0.0200 per GB + $0.0025 per 1,000 requests
    gb_cost = gb * deep_archive_retrieval_cost_gb
    cost_breakdown.append(f"Data Retrieval Cost: {gb} GB x ${deep_archive_retrieval_cost_gb} = ${gb_cost}")
    requests_cost = n_samples * deep_archive_request_cost
    cost_breakdown.append(f"Requests Cost (GET, SELECT): {n_samples} files x {deep_archive_request_cost} per request = ${requests_cost}")
    total_cost = gb_cost + requests_cost
    cost_breakdown.append(f"Total Data Retrieval Cost: ${gb_cost} + ${requests_cost} = ${total_cost}")
    return total_cost if total_cost and total_cost > 0 else 0


def calculate_data_transfer_cost(storage, gb, n_samples, times, requests_per_obj=2, cost_breakdown=[]):
    retrival_cost = 0
    total_cost = 0
    if storage != "Standard Storage":
        retrival_cost = calculate_data_retrival_cost(gb, n_samples, times, requests_per_obj, cost_breakdown=cost_breakdown)

    cost_breakdown.append("Data Transfer Cost Breakdown:")
    cost_breakdown.append(f"Data Transfer Out to Internet Cost: ${data_transfer_out_cost} per GB")
    cost_breakdown.append(f"GET and all other Requests Cost: ${get_select_1000_request_cost} per 1000 requests")
    # Data Transfer OUT to Internet: Cost = Data Transferred (GB) x $0.09 per GB
    # Data Transfer IN from Internet: No charge
    # GET and all other Requests: $0.0004 per 1,000 requests
    requests_cost = requests_per_obj * n_samples * get_select_request_cost
    cost_breakdown.append(f"Requests Cost (GET, SELECT): {n_samples} files x {get_select_request_cost} per request = ${requests_cost}")
    transfer_cost = gb * data_transfer_out_cost
    cost_breakdown.append(f"Data Transfer Out Cost: {gb} GB x ${data_transfer_out_cost} = ${transfer_cost}")

    if storage == "Standard Storage":
        total_cost = (requests_cost + transfer_cost) * times
        cost_breakdown.append(f"Total Data Transfer Cost: (${requests_cost} + ${transfer_cost}) x {times} Time(s) = ${total_cost}")
    else:
        total_cost = (requests_cost + transfer_cost + retrival_cost) * times
        cost_breakdown.append(f"Total Data Transfer Cost: (${requests_cost} + ${transfer_cost} + ${retrival_cost}) x {times} Time(s) = ${total_cost}")
    return total_cost if total_cost and total_cost > 0 else 0

def pie_chart(storage_cost, download_cost):
    fig = px.pie(
        values=[storage_cost, download_cost],
        names=["Storage Cost", "Download Cost"],
        title="Cost Distribution",
        labels={'Storage Cost':'Storage Cost (USD)', 'Download Cost':'Download Cost (USD)'}
    )
    fig.update_traces(hoverinfo='label', textinfo='value', textfont_size=20,
                  marker=dict(colors=["#E567CB", "#6070FA"], line=dict(color='#000000', width=1)))
    return fig

def bar_chart_distribution(data_array):
    data_array_copy = data_array.copy()

    fig = px.bar(data_array_copy, x="Month", y="Cost", title="Storage Cost Distribution by Month",
                 hover_data=['Month', 'Cost'],
             labels={'Cost':'Storage Cost (USD)', 'Month':'Months'})
    return fig
    
def bar_chart_accumulation(data_array):
    # manually copy to another array
    data_array_copy = data_array.copy()

    for i in range(1, len(data_array_copy)):
        data_array_copy[i]["Cost"] += data_array_copy[i-1]["Cost"]

    fig = px.bar(data_array_copy, x="Month", y="Cost", title="Accumulated Cost over Month",
                                  hover_data=['Month', 'Cost'],
             labels={'Cost':'Storage Cost (USD)', 'Month':'Months'})
    return fig

@reactive.effect
@reactive.event(input.reset)
def _():
    ui.update_numeric("s_samples", value=0)
    ui.update_numeric("s_size", value=0)
    ui.update_numeric("s_download", value=0)
    ui.update_numeric("s_download_times", value=0)
    ui.update_numeric("s_download_samples", value=0)
    ui.update_slider("s_duration", value=total_months)
    ui.update_checkbox_group("a_class", selected=storage_class)
    ui.update_select("currency", selected=currency)
    ui.update_radio_buttons("mode", selected=mode)

@reactive.effect
@reactive.event(input.show)
def _():
    m = ui.modal(
        ui.TagList(print_cost()),
        title="Cost Breakdown",
        easy_close=True,
        footer="GeDaC, 2024",
        size="l",
    )
    ui.modal_show(m)

@reactive.effect
@reactive.event(input.sample_info)
def _():
    m = ui.modal(
        ui.TagList(print_table()),
        title="Sequencing Data Size Summary Across Various Techniques",
        easy_close=True,
        footer="GeDaC, 2024",
        size="xl",
    )
    ui.modal_show(m)

def backup_cost():
    for i in calculate_info()["cost_breakdown"]:
        if i.endswith(":"):
            ui.HTML(f"<p style='font-weight: bold;'><u>{i}</u></p>")
        else:
            ui.HTML(f"<p>{i}</p>")

def print_cost():
    html_strings = [f"<p style='font-weight: bold;'><u>{i}</u></p>" if i.endswith(":") else f"<p>{i}</p>" for i in calculate_info()["cost_breakdown"]]
    big_string = "".join(html_strings)
    return ui.HTML(big_string)

def print_table():
    table = '<table style="border-collapse: collapse; width: 100%;">'
    table += '<tr style="background-color: #f2f2f2;">'
    table += '<th style="border: 1px solid black; padding: 8px;">Sequencing Type</th>'
    table += '<th style="border: 1px solid black; padding: 8px;">Coverage/Read Details</th>'
    table += '<th style="border: 1px solid black; padding: 8px;">Data Size</th>'
    table += '</tr>'
    for index, row in ngs_details.iterrows():
        table += '<tr>'
        table += f'<td style="border: 1px solid black; padding: 8px;">{row["Sequencing Type"]}</td>'
        table += f'<td style="border: 1px solid black; padding: 8px;">{row["Coverage/Read Details"]}</td>'
        table += f'<td style="border: 1px solid black; padding: 8px;">{row["Data Size"]}</td>'
        table += '</tr>'
    table += '</table>'
    return  ui.HTML(table)
