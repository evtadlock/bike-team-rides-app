from shiny import App, ui, render, reactive
from urllib.parse import parse_qs
import os
import re
import uuid
import datetime

from .database import (
    init_db,
    insert_signup,
    cancel_signup_by_token,
    list_signups,
)
from .email_utils import send_confirmation_email


# -----------------------
# Config via environment
# -----------------------
APP_TITLE = os.getenv("TEAMUGLY_APP_TITLE", "Team Ugly Training Rides")
APP_URL = os.getenv("TEAMUGLY_APP_URL", "https://YOUR-APP-URL")  # used in emails + QR
DB_PATH = os.getenv("TEAMUGLY_DB_PATH", "data/teamugly.sqlite")

ADMIN_PASSWORD = os.getenv("TEAMUGLY_ADMIN_PASSWORD", "change_me")
TIMEZONE_LABEL = os.getenv("TEAMUGLY_TIMEZONE_LABEL", "America/Chicago")

# Create DB on startup
init_db(DB_PATH)


def is_valid_email(email: str) -> bool:
    if email is None:
        return False
    email = email.strip()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def now_utc_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


# -----------------------
# UI
# -----------------------
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(
            """
            .hero { padding: 18px 20px; border-radius: 14px; background: #f6f6f6; }
            .small { color: #666; font-size: 0.95em; }
            .okbox { padding: 10px 12px; border-radius: 12px; background: #eef6ff; }
            .warnbox { padding: 10px 12px; border-radius: 12px; background: #fff3cd; }
            .errbox { padding: 10px 12px; border-radius: 12px; background: #fdecea; }
            .pill { display:inline-block; padding: 3px 10px; border-radius: 999px; background:#eee; margin-right:6px; }
            """
        )
    ),
    ui.div(
        {"class": "hero"},
        ui.h2(APP_TITLE),
        ui.p(
            "Informal, voluntary group rides coordinated by Team Ugly participants. "
            "This page is for RSVP coordination and email updates."
        ),
        ui.p(
            {"class": "small"},
            "For official Bike MS event registration, use the National MS Society Bike MS website.",
        ),
        ui.div(
            {"class": "small"},
            ui.span({"class": "pill"}, "RSVP"),
            ui.span({"class": "pill"}, "Email confirmation"),
            ui.span({"class": "pill"}, "Self-cancel"),
            ui.span({"class": "pill"}, f"Timezone: {TIMEZONE_LABEL}"),
        ),
    ),
    ui.br(),
    ui.navset_tab(
        ui.nav(
            "Sign Up",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Ride details"),
                    ui.input_select(
                        "ride_name",
                        "Ride",
                        choices={
                            "Saturday Training Ride": "Saturday Training Ride",
                            "Weeknight Ride": "Weeknight Ride",
                            "Long Ride": "Long Ride",
                            "Social / Coffee Ride": "Social / Coffee Ride",
                        },
                        selected="Saturday Training Ride",
                    ),
                    ui.input_date(
                        "ride_date",
                        "Ride date",
                        value=str(datetime.date.today() + datetime.timedelta(days=7)),
                    ),
                    ui.input_text("start_time", "Start time", value="7:00 AM"),
                    ui.input_text(
                        "meeting_point",
                        "Meeting point",
                        placeholder="Example: Katy Trail Outpost, Plano",
                    ),
                    ui.input_text(
                        "route_link",
                        "Route link (optional)",
                        placeholder="Strava, RideWithGPS, Google Maps",
                    ),
                ),
                ui.card(
                    ui.card_header("Your info"),
                    ui.input_text("full_name", "Full name"),
                    ui.input_text("email", "Email"),
                    ui.input_text("phone", "Phone (optional)"),
                    ui.input_text("city", "City (optional)"),
                    ui.input_text_area(
                        "notes",
                        "Notes (optional)",
                        placeholder="Questions, first time riding, anything helpful",
                        rows=4,
                    ),
                    ui.input_checkbox(
                        "acknowledge",
                        "I understand this is an informal group ride and I am responsible for my own safety and equipment.",
                        value=False,
                    ),
                    ui.br(),
                    ui.input_action_button("submit", "Submit RSVP", class_="btn-primary"),
                    ui.br(),
                    ui.output_ui("public_status"),
                ),
            ),
        ),
        ui.nav(
            "Cancel RSVP",
            ui.card(
                ui.card_header("Cancel using your cancellation code"),
                ui.p(
                    {"class": "small"},
                    "If you clicked the cancel link in your email, you may already be cancelled. "
                    "If you have a cancellation code, paste it below.",
                ),
                ui.input_text(
                    "cancel_token_input",
                    "Cancellation code",
                    placeholder="Example: 3c5b7f7e-...",
                ),
                ui.input_action_button("cancel_btn", "Cancel RSVP"),
                ui.br(),
                ui.output_ui("cancel_status"),
            ),
        ),
        ui.nav(
            "Admin",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Admin login"),
                    ui.p({"class": "small"}, "Enter the admin password to view/export the roster."),
                    ui.input_password("admin_pw", "Admin password"),
                    ui.input_action_button("admin_unlock", "Unlock"),
                    ui.br(),
                    ui.output_ui("admin_status"),
                ),
                ui.card(
                    ui.card_header("Roster"),
                    ui.output_data_frame("roster_table"),
                    ui.br(),
                    ui.download_button("download_csv", "Download CSV"),
                ),
            ),
        ),
    ),
)


# -----------------------
# Server
# -----------------------
def server(input, output, session):
    public_msg = reactive.Value(None)
    cancel_msg = reactive.Value(None)
    admin_unlocked = reactive.Value(False)
    admin_msg = reactive.Value("Locked.")

    # Handle cancel token via URL: ?cancel=<token>
    @reactive.effect
    def _handle_url_cancel():
        qs = parse_qs(session.clientdata.url_search.get() or "")
        token = None
        if "cancel" in qs and len(qs["cancel"]) > 0:
            token = qs["cancel"][0]

        if token:
            cancelled = cancel_signup_by_token(DB_PATH, token)
            if cancelled:
                cancel_msg.set(ui.div({"class": "okbox"}, "Your RSVP has been cancelled."))
            else:
                cancel_msg.set(ui.div({"class": "warnbox"}, "Cancel link already used or not found."))

    @output
    @render.ui
    def public_status():
        return public_msg.get()

    @output
    @render.ui
    def cancel_status():
        return cancel_msg.get()

    @output
    @render.ui
    def admin_status():
        return ui.div({"class": "small"}, admin_msg.get())

    @reactive.event(input.admin_unlock)
    def _unlock_admin():
        pw = (input.admin_pw() or "").strip()
        if pw and pw == ADMIN_PASSWORD:
            admin_unlocked.set(True)
            admin_msg.set("Unlocked.")
        else:
            admin_unlocked.set(False)
            admin_msg.set("Locked. Incorrect password.")

    @reactive.event(input.submit)
    def _submit_rsvp():
        public_msg.set(None)

        name = (input.full_name() or "").strip()
        email = (input.email() or "").strip()

        if name == "":
            public_msg.set(ui.div({"class": "errbox"}, "Please enter your full name."))
            return
        if not is_valid_email(email):
            public_msg.set(ui.div({"class": "errbox"}, "Please enter a valid email."))
            return
        if not bool(input.acknowledge()):
            public_msg.set(ui.div({"class": "errbox"}, "Please check the acknowledgement box."))
            return

        ride_name = input.ride_name()
        ride_date = str(input.ride_date())
        start_time = (input.start_time() or "").strip()
        meeting_point = (input.meeting_point() or "").strip()
        route_link = (input.route_link() or "").strip()

        phone = (input.phone() or "").strip()
        city = (input.city() or "").strip()
        notes = (input.notes() or "").strip()

        token = str(uuid.uuid4())
        created_utc = now_utc_iso()

        insert_signup(
            db_path=DB_PATH,
            created_utc=created_utc,
            ride_name=ride_name,
            ride_date=ride_date,
            start_time=start_time,
            meeting_point=meeting_point,
            route_link=route_link,
            full_name=name,
            email=email,
            phone=phone,
            city=city,
            notes=notes,
            acknowledge=1,
            cancel_token=token,
        )

        cancel_link = f"{APP_URL}?cancel={token}"

        email_sent = False
        try:
            send_confirmation_email(
                to_email=email,
                full_name=name,
                ride_name=ride_name,
                ride_date=ride_date,
                start_time=start_time,
                meeting_point=meeting_point,
                route_link=route_link,
                cancel_link=cancel_link,
            )
            email_sent = True
        except Exception:
            email_sent = False

        if email_sent:
            public_msg.set(
                ui.div(
                    {"class": "okbox"},
                    ui.p("RSVP received. A confirmation email has been sent."),
                    ui.p({"class": "small"}, "Keep that email for your self-cancel link."),
                )
            )
        else:
            public_msg.set(
                ui.div(
                    {"class": "warnbox"},
                    ui.p("RSVP saved, but email could not be sent from the server."),
                    ui.p({"class": "small"}, f"Your cancellation code is: {token}"),
                )
            )

    @reactive.event(input.cancel_btn)
    def _cancel_manual():
        token = (input.cancel_token_input() or "").strip()
        if token == "":
            cancel_msg.set(ui.div({"class": "errbox"}, "Please paste your cancellation code."))
            return

        cancelled = cancel_signup_by_token(DB_PATH, token)
        if cancelled:
            cancel_msg.set(ui.div({"class": "okbox"}, "Your RSVP has been cancelled."))
        else:
            cancel_msg.set(ui.div({"class": "warnbox"}, "Not found or already cancelled."))

    @output
    @render.data_frame
    def roster_table():
        if not admin_unlocked.get():
            return render.DataGrid([["Locked."]], selection_mode="none", height="240px")

        rows = list_signups(DB_PATH)
        safe_rows = [
            {
                "created_utc": r["created_utc"],
                "ride_name": r["ride_name"],
                "ride_date": r["ride_date"],
                "start_time": r["start_time"],
                "meeting_point": r["meeting_point"],
                "full_name": r["full_name"],
                "email": r["email"],
                "phone": r["phone"],
                "city": r["city"],
                "notes": r["notes"],
                "status": r["status"],
            }
            for r in rows
        ]
        return render.DataGrid(safe_rows, selection_mode="none", height="520px")

    @output
    @render.download(filename=lambda: f"teamugly_roster_{datetime.date.today().isoformat()}.csv")
    def download_csv():
        if not admin_unlocked.get():
            yield "created_utc,ride_name,ride_date,start_time,meeting_point,full_name,email,phone,city,notes,status\n"
            return

        rows = list_signups(DB_PATH)
        header = "created_utc,ride_name,ride_date,start_time,meeting_point,route_link,full_name,email,phone,city,notes,status\n"
        yield header

        def esc(x):
            s = "" if x is None else str(x)
            s = s.replace('"', '""')
            return f'"{s}"'

        for r in rows:
            yield ",".join(
                [
                    esc(r.get("created_utc")),
                    esc(r.get("ride_name")),
                    esc(r.get("ride_date")),
                    esc(r.get("start_time")),
                    esc(r.get("meeting_point")),
                    esc(r.get("route_link")),
                    esc(r.get("full_name")),
                    esc(r.get("email")),
                    esc(r.get("phone")),
                    esc(r.get("city")),
                    esc(r.get("notes")),
                    esc(r.get("status")),
                ]
            ) + "\n"


app = App(app_ui, server)