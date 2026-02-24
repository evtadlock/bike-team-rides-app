import base64
import csv
import os
import urllib.parse
import pandas as pd
from shiny import App, ui, render, reactive

from database import (
    init_db,
    create_ride,
    list_rides,
    get_ride_details,
    signup,
    cancel_signup,
    roster,
    delete_ride
)

init_db()

ADMIN_PASS  = "passwordmakeitsocomplicated!"
TEAM_LINK    = "https://tinyurl.com/TeamUglyRides"
BIKEMS_LINK  = "https://events.nationalmssociety.org/teams/TeamUgly"
MAILING_CSV  = "contacts.csv"

NAVY   = "#002D5C"
BLUE   = "#0078BF"
ORANGE = "#F47920"
WHITE  = "#FFFFFF"

# ---------- ENCODE TEAM PHOTO ----------
def encode_image(path):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"

team_photo_src = encode_image("team_photo.png")

# ---------- MAILING LIST HELPERS ----------
def load_contacts():
    if not os.path.exists(MAILING_CSV):
        return []
    contacts = []
    with open(MAILING_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = (row.get("Email") or row.get("email") or row.get("EMAIL") or "").strip()
            first = (row.get("First Name") or row.get("first name") or row.get("first") or "").strip()
            if email:
                contacts.append({"email": email, "first": first})
    return contacts


def build_gmail_url(emails, subject, body):
    params = urllib.parse.urlencode({
        "view": "cm",
        "to":   ",".join(emails),
        "su":   subject,
        "body": body,
    })
    return f"https://mail.google.com/mail/?{params}"


def build_mailto_url(emails, subject, body):
    return (
        "mailto:?bcc=" + urllib.parse.quote(",".join(emails)) +
        "&subject=" + urllib.parse.quote(subject) +
        "&body=" + urllib.parse.quote(body)
    )


def build_notify_urls(ride_name, ride_date, ride_time, ride_loc, ride_route):
    contacts = load_contacts()
    if not contacts:
        return None, None, None
    emails  = [c["email"] for c in contacts]
    subject = f"Team Ugly Training Ride: {ride_name} on {ride_date}"
    body = (
        f"Hey Team Ugly!\n\n"
        f"A training ride has been posted:\n\n"
        f"  Ride:          {ride_name}\n"
        f"  Date:          {ride_date}\n"
        f"  Time:          {ride_time}\n"
        f"  Meeting Point: {ride_loc}\n"
        f"  GPS Route:     {ride_route}\n\n"
        f"Sign up for the ride at:\n"
        f"{TEAM_LINK}\n\n"
        f"Not yet on Team Ugly for Bike MS? Join us here:\n"
        f"{BIKEMS_LINK}\n\n"
        f"See you out there!\n— Team Ugly"
    )
    return (
        build_gmail_url(emails, subject, body),
        build_mailto_url(emails, subject, body),
        ", ".join(emails)
    )


# ---------- NOTIFY PANEL ----------
def notify_panel(gmail_url, mailto_url, email_str):
    if not gmail_url:
        return ui.p("No contacts.csv found — add one to enable notifications.",
                    style="color:#aad4f0; font-size:13px;")
    count = len(email_str.split(","))
    return ui.div(
        ui.p(
            f"{count} teammates on the mailing list. Choose how to notify them:",
            style="color:#aad4f0; font-size:13px; margin-bottom:10px;"
        ),
        ui.div(
            ui.a(
                "Open Gmail",
                href=gmail_url,
                target="_blank",
                style=(
                    f"display:block; text-align:center; background:#D44638; color:{WHITE}; "
                    "padding:12px; border-radius:5px; text-decoration:none; "
                    "font-weight:700; font-size:15px; margin-bottom:10px;"
                )
            ),
            ui.a(
                "Open Email App",
                href=mailto_url,
                style=(
                    f"display:block; text-align:center; background:#555; color:{WHITE}; "
                    "padding:12px; border-radius:5px; text-decoration:none; "
                    "font-weight:700; font-size:15px; margin-bottom:10px;"
                )
            ),
            ui.tags.button(
                "Copy Email List",
                onclick=f"""
                    navigator.clipboard.writeText({repr(email_str)}).then(function() {{
                        var btn = this;
                        btn.innerText = 'Copied!';
                        btn.style.background = '#2a7a2a';
                        setTimeout(function() {{
                            btn.innerText = 'Copy Email List';
                            btn.style.background = '#F47920';
                        }}, 2500);
                    }}.bind(this));
                """,
                style=(
                    f"width:100%; background:{ORANGE}; color:{WHITE}; border:none; "
                    "padding:12px; border-radius:5px; "
                    "font-weight:700; font-size:15px; cursor:pointer; margin-bottom:10px;"
                )
            ),
            ui.div(
                ui.p("Or copy manually:", style="color:#aad4f0; font-size:12px; margin:4px 0;"),
                ui.tags.textarea(
                    email_str,
                    rows="4",
                    readonly=True,
                    style=(
                        "width:100%; background:#003f7a; color:#fff; "
                        "border:1px solid #0078BF; border-radius:5px; "
                        "padding:8px; font-size:12px; resize:vertical; box-sizing:border-box;"
                    )
                )
            )
        )
    )


# ---------- GLOBAL CSS ----------
global_css = ui.tags.style(f"""
    /* ── Base ── */
    * {{ box-sizing: border-box; }}

    body {{
        background-color: {NAVY};
        font-family: 'Segoe UI', Arial, sans-serif;
        color: {WHITE};
        margin: 0;
        padding: 0;
    }}

    .container-fluid {{
        padding: 12px 16px;
        max-width: 100%;
        overflow-x: hidden;
    }}

    /* ── Banner ── */
    .tu-banner {{
        background: linear-gradient(135deg, {BLUE}, {NAVY});
        border-bottom: 4px solid {ORANGE};
        padding: 18px 16px;
        text-align: center;
        border-radius: 8px 8px 0 0;
        margin-bottom: 0;
    }}
    .tu-banner h1 {{
        color: {WHITE};
        margin: 0;
        font-size: clamp(1.1rem, 4vw, 1.9rem);
        font-weight: 800;
        letter-spacing: 0.3px;
        line-height: 1.3;
    }}

    /* ── Tabs ── */
    .nav-tabs {{
        border-bottom: 2px solid {BLUE};
        margin-bottom: 0;
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
    }}
    .nav-tabs::-webkit-scrollbar {{ display: none; }}
    .nav-tabs .nav-link {{
        color: #aac8e0;
        background: transparent;
        border: none;
        font-weight: 600;
        font-size: clamp(12px, 3vw, 15px);
        padding: 10px 14px;
        border-radius: 0;
        white-space: nowrap;
    }}
    .nav-tabs .nav-link:hover {{ color: {WHITE}; background: rgba(0,120,191,0.2); }}
    .nav-tabs .nav-link.active {{
        color: {WHITE};
        background: {BLUE};
        border-bottom: 3px solid {ORANGE};
    }}

    /* ── Tab content ── */
    .tab-content {{
        background: rgba(0,45,92,0.6);
        border: 1px solid {BLUE};
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 14px;
    }}

    /* ── Layout: sidebar stacks below on mobile ── */
    .tu-layout {{
        display: flex;
        flex-direction: row !important;
        align-items: flex-start;
        gap: 16px;
        margin-top: 10px;
        flex-wrap: nowrap;
    }}
    .tu-main {{ flex: 1; min-width: 0; }}
    .tu-sidebar {{
        width: 300px;
        min-width: 280px;
        flex-shrink: 0;
    }}
    .tu-sidebar img {{
        max-height: 200px;
        width: 100%;
        object-fit: cover;
        object-position: center center;
    }}

    @media (max-width: 700px) {{
        .tu-layout {{
            flex-direction: column !important;
        }}
        .tu-sidebar {{
            width: 100%;
            min-width: 0;
        }}
        .tu-sidebar img {{
            max-height: none;
        }}
        .container-fluid {{
            padding: 8px 10px;
        }}
        .tab-content {{
            padding: 10px;
        }}
    }}

    /* ── Forms ── */
    label {{ color: {WHITE} !important; font-weight: 600; }}

    input[type="text"],
    input[type="password"],
    input[type="date"],
    select {{
        background-color: #003f7a !important;
        color: {WHITE} !important;
        border: 1px solid {BLUE} !important;
        border-radius: 5px !important;
        width: 100% !important;
        font-size: 16px !important;  /* prevents iOS zoom on focus */
    }}
    input[type="text"]::placeholder,
    input[type="password"]::placeholder {{
        color: #aac8e0 !important;
    }}
    select option {{ background-color: {NAVY}; color: {WHITE}; }}

    /* ── Ride list box ── */
    #ride_select {{
        width: 100% !important;
        min-width: 100% !important;
        font-size: 15px !important;
    }}

    /* ── Buttons — full width on mobile ── */
    .tu-btn {{
        display: block;
        width: 100%;
        text-align: center;
        padding: 13px 20px;
        border: none;
        border-radius: 6px;
        font-weight: 700;
        font-size: 16px;
        cursor: pointer;
        margin-top: 10px;
        -webkit-appearance: none;
    }}

    /* ── Table ── */
    .table-responsive {{
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }}
    table {{ width: 100%; border-collapse: collapse; color: {WHITE}; }}
    table thead th {{
        background-color: {BLUE};
        color: {WHITE};
        padding: 10px 12px;
        text-align: left;
        font-weight: 700;
        font-size: 14px;
        white-space: nowrap;
    }}
    table tbody tr:nth-child(even) {{ background-color: rgba(0,120,191,0.15); }}
    table tbody tr:nth-child(odd)  {{ background-color: rgba(0,45,92,0.5); }}
    table tbody td {{
        padding: 8px 12px;
        border-bottom: 1px solid rgba(0,120,191,0.3);
        font-size: 14px;
    }}

    .shiny-text-output {{ color: {WHITE}; }}
    hr {{ border-color: {BLUE}; opacity: 0.5; margin: 16px 0; }}

    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-track {{ background: {NAVY}; }}
    ::-webkit-scrollbar-thumb {{ background: {BLUE}; border-radius: 3px; }}
""")


# ---------- SIDEBAR PROMO ----------
def promo_sidebar():
    return ui.div(
        # Promo text and button ABOVE photo
        ui.div(
            ui.h4("Ride for a Cause!", style=f"color:{ORANGE}; margin-top:0; font-size:1.05rem;"),
            ui.p(
                "Haven't signed up for Bike MS yet? Come ride with us — "
                "join Team Ugly and help end MS!",
                style=f"font-size:14px; color:{WHITE}; line-height:1.5; margin:6px 0;"
            ),
            ui.a(
                "Join Team Ugly on Bike MS",
                href=BIKEMS_LINK,
                target="_blank",
                style=(
                    f"display:block; text-align:center; background:{ORANGE}; "
                    f"color:{WHITE}; padding:12px; border-radius:6px; "
                    "text-decoration:none; font-weight:bold; font-size:15px; "
                    "margin-top:10px;"
                )
            ),
            style=(
                f"background:rgba(0,120,191,0.2); border:2px solid {BLUE}; "
                "border-radius:8px; padding:14px; margin-bottom:12px;"
            )
        ),
        # Photo below — constrained on desktop, full width on mobile
        ui.img(
            src=team_photo_src,
            style="width:100%; border-radius:8px; border:2px solid #0078BF; display:block;"
        ),
        cls="tu-sidebar",
        style="padding:4px;"
    )


def with_sidebar(*content):
    return ui.div(
        ui.div(*content, cls="tu-main"),
        promo_sidebar(),
        cls="tu-layout"
    )


# ---------- BANNER ----------
banner = ui.div(
    ui.h1("Team Ugly Bike MS Round Up 2026 Training Rides"),
    cls="tu-banner"
)


# ---------- UI ----------
app_ui = ui.page_fluid(

    # Viewport meta tag for proper mobile scaling
    ui.tags.head(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1.0")
    ),

    global_css,
    banner,

    ui.navset_tab(

        # ---- SIGN UP ----
        ui.nav_panel(
            "Sign Up",
            with_sidebar(
                ui.output_ui("ride_list"),
                ui.output_ui("ride_details"),
                ui.input_text("name", "Full Name"),
                ui.input_action_button(
                    "signup_btn", "Sign Up",
                    style=f"background:{ORANGE}; color:{WHITE}; border:none; padding:13px 20px; "
                          "border-radius:6px; width:100%; font-weight:700; font-size:16px; "
                          "cursor:pointer; margin-top:10px; display:block;"
                ),
                ui.output_ui("signup_msg")
            )
        ),

        # ---- CANCEL ----
        ui.nav_panel(
            "Cancel Registration",
            with_sidebar(
                ui.input_text("cancel_code", "Confirmation Number"),
                ui.input_action_button(
                    "cancel_btn", "Cancel My Spot",
                    style=f"background:#555; color:{WHITE}; border:none; padding:13px 20px; "
                          "border-radius:6px; width:100%; font-weight:700; font-size:16px; "
                          "cursor:pointer; margin-top:10px; display:block;"
                ),
                ui.output_text("cancel_msg")
            )
        ),

        # ---- ROSTER ----
        ui.nav_panel(
            "Roster",
            with_sidebar(
                ui.div(
                    ui.output_table("roster_table"),
                    cls="table-responsive"
                )
            )
        ),

        # ---- ADMIN ----
        ui.nav_panel(
            "Admin",
            with_sidebar(
                ui.input_password("admin_pass", "Password"),
                ui.output_ui("admin_panel")
            )
        )
    )
)


# ---------- SERVER ----------
def server(input, output, session):

    signup_msg_val    = reactive.Value("")
    cancel_msg_val    = reactive.Value("")
    admin_msg_val     = reactive.Value("")
    delete_msg_val    = reactive.Value("")
    notify_gmail_val  = reactive.Value("")
    notify_mailto_val = reactive.Value("")
    notify_emails_val = reactive.Value("")

    # ---- RIDE LIST ----
    @output
    @render.ui
    def ride_list():
        rides = list_rides()
        if not rides:
            return ui.p("No rides available.", style="color:#aad4f0;")
        return ui.div(
            ui.input_select(
                "ride_select",
                "Select Ride",
                {str(r[0]): f"{r[1]} — {r[2]}" for r in rides},
                size=min(len(rides), 8),
                selectize=False
            ),
            style=(
                "width:100%; overflow-x:hidden; overflow-y:auto; "
                "border:1px solid #0078BF; border-radius:6px; "
                "background:#003f7a; padding:4px;"
            )
        )

    # ---- RIDE DETAILS ----
    @output
    @render.ui
    def ride_details():
        if "ride_select" not in input:
            return ui.p("Select a ride.", style="color:#aad4f0;")
        ride_id = input.ride_select()
        if not ride_id:
            return ui.p("Select a ride.", style="color:#aad4f0;")
        details = get_ride_details(ride_id)
        if not details:
            return ui.p("No details.", style="color:#aad4f0;")
        name, date, time, loc, route = details
        return ui.div(
            ui.h4(name, style=f"color:{ORANGE}; margin-bottom:6px; font-size:1rem;"),
            ui.p(f"Date: {date}",         style=f"color:{WHITE}; margin:4px 0;"),
            ui.p(f"Time: {time}",         style=f"color:{WHITE}; margin:4px 0;"),
            ui.p(f"Meeting Point: {loc}", style=f"color:{WHITE}; margin:4px 0;"),
            ui.a("View GPS Route", href=route, target="_blank",
                 style=f"color:{ORANGE}; font-weight:bold; font-size:15px;")
            if route else ui.p("No GPS link.", style="color:#aad4f0;"),
            style=(
                f"background:rgba(0,120,191,0.15); border-left:4px solid {BLUE}; "
                "padding:12px 14px; border-radius:6px; margin:10px 0;"
            )
        )

    # ---- SIGNUP ----
    @reactive.effect
    @reactive.event(input.signup_btn)
    def do_signup():
        if "ride_select" not in input:
            signup_msg_val.set("Select a ride.")
            return
        ride_id = input.ride_select()
        name    = input.name()
        if not ride_id:
            signup_msg_val.set("Select a ride.")
            return
        if not name:
            signup_msg_val.set("Enter your name.")
            return
        code = signup(ride_id, name)
        signup_msg_val.set(f"Confirmed! Your confirmation number is: {code}")

    @output
    @render.ui
    def signup_msg():
        msg = signup_msg_val.get()
        if not msg:
            return ui.div()
        return ui.div(
            ui.p(msg, style="font-size:16px; font-weight:bold; color:#5ddb8a; margin-bottom:10px;"),
            ui.div(
                ui.p(
                    "⚠️  Please save your confirmation number — it is required to cancel your spot.",
                    style=f"color:{WHITE}; font-weight:600; margin:0 0 8px 0; font-size:14px;"
                ),
                ui.p(
                    "Disclaimer: By signing up, you acknowledge that participation in "
                    "Team Ugly training rides is at your own risk. Any incidents, accidents, "
                    "or occurrences during the ride are the sole responsibility of the rider. "
                    "Team Ugly and its organizers assume no liability.",
                    style="color:#aad4f0; font-size:12px; margin:0; line-height:1.5;"
                ),
                style=(
                    f"background:rgba(0,120,191,0.2); border-left:4px solid {ORANGE}; "
                    "padding:12px 14px; border-radius:6px;"
                )
            )
        )

    # ---- CANCEL ----
    @reactive.effect
    @reactive.event(input.cancel_btn)
    def do_cancel():
        code = input.cancel_code()
        if not code:
            cancel_msg_val.set("Enter confirmation number.")
            return
        removed = cancel_signup(code)
        cancel_msg_val.set("Code not found." if removed == 0 else "You have been removed from the ride.")

    @output
    @render.text
    def cancel_msg():
        return cancel_msg_val.get()

    # ---- ADMIN CREATE ----
    @reactive.effect
    @reactive.event(input.create_btn)
    def do_create():
        name = input.ride_name()
        if not name:
            admin_msg_val.set("Enter a ride name.")
            return
        create_ride(name, str(input.ride_date()), input.ride_time(),
                    input.ride_loc(), input.ride_route())
        admin_msg_val.set(f"Ride '{name}' created successfully.")

    @output
    @render.text
    def admin_msg():
        return admin_msg_val.get()

    # ---- ADMIN PANEL (server-side password check) ----
    @output
    @render.ui
    def admin_panel():
        pw = input.admin_pass()
        if pw != ADMIN_PASS:
            if pw:
                return ui.p("Incorrect password.", style="color:#ff6b6b; margin-top:8px;")
            return ui.div()

        btn_style = (
            f"border:none; padding:13px 20px; border-radius:6px; width:100%; "
            "font-weight:700; font-size:16px; cursor:pointer; margin-top:10px; display:block;"
        )
        return ui.div(
            # -- Create Ride --
            ui.h4("Create Ride", style=f"color:{ORANGE}; margin-top:16px;"),
            ui.input_text("ride_name", "Ride Name"),
            ui.input_date("ride_date", "Ride Date"),
            ui.input_text("ride_time", "Start Time"),
            ui.input_text("ride_loc", "Meeting Point"),
            ui.input_text("ride_route", "GPS Link"),
            ui.input_action_button(
                "create_btn", "Create Ride",
                style=f"background:{BLUE}; color:{WHITE}; " + btn_style
            ),
            ui.output_text("admin_msg"),

            ui.hr(),

            # -- Notify Team --
            ui.h4("Notify Team", style=f"color:{ORANGE};"),
            ui.p("Select any ride and notify teammates.",
                 style="color:#aad4f0; font-size:13px; margin-bottom:10px;"),
            ui.output_ui("notify_ride_select"),
            ui.input_action_button(
                "notify_btn", "Prepare Notification",
                style=f"background:{ORANGE}; color:{WHITE}; " + btn_style
            ),
            ui.output_ui("notify_panel_output"),

            ui.hr(),

            # -- Delete Ride --
            ui.h4("Delete Ride", style=f"color:{ORANGE};"),
            ui.output_ui("admin_ride_list"),
            ui.input_action_button(
                "delete_btn", "Delete Ride",
                style="background:#8B0000; color:white; " + btn_style
            ),
            ui.output_text("delete_msg")
        )

    # ---- NOTIFY RIDE SELECTOR ----
    @output
    @render.ui
    def notify_ride_select():
        rides = list_rides()
        if not rides:
            return ui.p("No rides yet.", style="color:#aad4f0;")
        return ui.input_select(
            "notify_ride_id",
            "Select Ride to Notify About",
            {str(r[0]): f"{r[1]} — {r[2]}" for r in rides}
        )

    # ---- PREPARE NOTIFICATION ----
    @reactive.effect
    @reactive.event(input.notify_btn)
    def do_notify():
        if "notify_ride_id" not in input:
            return
        ride_id = input.notify_ride_id()
        details = get_ride_details(ride_id)
        if not details:
            return
        r_name, r_date, r_time, r_loc, r_route = details
        gmail, mailto, emails = build_notify_urls(r_name, r_date, r_time, r_loc, r_route)
        notify_gmail_val.set(gmail or "")
        notify_mailto_val.set(mailto or "")
        notify_emails_val.set(emails or "")

    # ---- NOTIFY PANEL OUTPUT ----
    @output
    @render.ui
    def notify_panel_output():
        gmail  = notify_gmail_val.get()
        mailto = notify_mailto_val.get()
        emails = notify_emails_val.get()
        if not gmail and not emails:
            return ui.div()
        return ui.div(
            notify_panel(gmail, mailto, emails),
            style=(
                f"background:rgba(0,120,191,0.1); border:1px solid {BLUE}; "
                "border-radius:8px; padding:14px; margin-top:12px;"
            )
        )

    # ---- ADMIN RIDE LIST ----
    @output
    @render.ui
    def admin_ride_list():
        rides = list_rides()
        if not rides:
            return ui.p("No rides.", style="color:#aad4f0;")
        return ui.input_select(
            "admin_ride_select",
            "Select Ride to Delete",
            {str(r[0]): f"{r[1]} — {r[2]}" for r in rides}
        )

    # ---- DELETE ----
    @reactive.effect
    @reactive.event(input.delete_btn)
    def do_delete():
        if "admin_ride_select" not in input:
            delete_msg_val.set("Select a ride.")
            return
        delete_ride(input.admin_ride_select())
        delete_msg_val.set("Ride deleted.")

    @output
    @render.text
    def delete_msg():
        return delete_msg_val.get()

    # ---- ROSTER ----
    @output
    @render.table
    def roster_table():
        rows = roster()
        return pd.DataFrame(rows, columns=["Ride", "Date", "Name"])


app = App(app_ui, server)