# sportinclujnapoca.ro booking automation — status notes

Location: /home/tdascal/Work/booking (book.py, .env [gitignored], .venv). Python + Selenium, system /usr/bin/chromium (override CHROME_BIN), browser left open (detach).

## Flow (verified working, Monday 2026-10-26 19:00 test booked)
1. /login: input[name=email], input[name=password], button[type=submit] (JS click; cookie banner "rcc-confirm-button" can overlap).
2. /reservations/table-tennis?preferredSportComplex=la-terenuri-base
3. Week header "12 Octombrie 2026 - 18 Octombrie 2026" with next-arrow button; day buttons contain h6 day number (disabled if past/unavailable). Click next N weeks, then the day.
4. Time slots: span "HH:00" inside div[role=button]; DISABLED slots have no role=button. Court dropdown not required.
5. Click slot -> form submit button "Rezervă" -> confirmation view (same URL): 3 checkboxes -> button "Confirmă rezervarea".
6. Wait POST_CONFIRM_WAIT (15s) after confirm. NEVER open another session/login right after (race condition blocks the reservation).

## Config (env / .env)
SPORT_EMAIL, SPORT_PASSWORD, SLOT (default 19:00), WEEKDAY (0=Mon..6=Sun, default 2=Wed), WEEKS_AHEAD (default 2), POST_CONFIRM_WAIT (15), CHROME_BIN.
Target date = weekday of this week + WEEKS_AHEAD weeks. Exits with message if slot disabled / Rezervă disabled.

## Site rules
Max 14 days in advance; one booking per sport per week per player; table tennis needs 2 participants (invite within 2h); cancel up to 3h before.
/my-reservations only showed past reservations (couldn't verify upcoming there).

## Windows notes
Install Python+Chrome, new venv, pip install selenium python-dotenv, recreate .env, set CHROME_BIN or remove /usr/bin/chromium default.

## Next topic (user, later)
How and when the script is executed (scheduling).
