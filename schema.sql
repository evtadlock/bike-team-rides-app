CREATE TABLE IF NOT EXISTS signups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_utc TEXT NOT NULL,

    ride_name TEXT NOT NULL,
    ride_date TEXT NOT NULL,
    start_time TEXT,
    meeting_point TEXT,
    route_link TEXT,

    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    city TEXT,
    notes TEXT,

    acknowledge INTEGER NOT NULL DEFAULT 0,

    cancel_token TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE INDEX IF NOT EXISTS idx_signups_ride_date ON signups(ride_date);
CREATE INDEX IF NOT EXISTS idx_signups_cancel_token ON signups(cancel_token);