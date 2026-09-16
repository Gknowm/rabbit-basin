# Rabbit Basin Field Map

An offline map for sunstone claim country in Lake County, Oregon. Topo and
imagery, DOGAMI geology, BLM land management, and active mining claims — all
saved on the phone so it works with no signal.

Four files of code and one script. No server, no account, no app store.

---

## What you need

A computer with Python 3 on it. Macs already have it. On Windows, get it from
python.org and tick "Add Python to PATH" during install.

To check: open Terminal (Mac) or Command Prompt (Windows) and type

    python3 --version

If you see a number, you're set.

---

## Step 1 — Get the data

In Terminal, go to this folder and run:

    python3 fetch.py

It downloads four datasets and the mapping library, and prints what it got.
Two or three minutes on a decent connection. You should end up with:

    data/geology.geojson
    data/claims.geojson
    data/ownership.geojson
    data/plss.geojson
    vendor/maplibre-gl.js
    vendor/maplibre-gl.css

If something fails, run `python3 fetch.py --check` to see which source is down.
Government services move occasionally; the fix is changing one line in `fetch.py`,
and the script tells you which one.

**To cover different ground**, open `fetch.py`, change the `BBOX` line near the
top, and run it again. Also change `START` in `index.html` so the map opens there.

---

## Step 2 — Look at it on your computer

You can't just double-click `index.html` — browsers block the offline machinery
on files opened directly. Start a tiny local server instead:

    python3 -m http.server 8000

Then open **http://localhost:8000** in your browser. Stop it with Ctrl-C.

Check that all four layers show feature counts in the Layers panel rather than
"Not downloaded yet."

---

## Step 3 — Put it on your phone

The map has to live at a web address for the offline part to work. GitHub Pages
is free and takes about five minutes.

1. Make a free account at github.com.
2. Click **+** → **New repository**. Name it `rabbit-basin`. Make it **Public**.
   Don't add a README — you have one.
3. On the new repo page, click **uploading an existing file**.
4. Drag in everything from this folder, including the `data` and `vendor`
   folders. Click **Commit changes**.
5. Go to **Settings** → **Pages**. Under Source pick **Deploy from a branch**,
   branch **main**, folder **/ (root)**. Save.
6. Wait a minute or two. Your address appears at the top of that page — something
   like `https://yourname.github.io/rabbit-basin/`.

Open that address on your phone.

- **iPhone:** Safari → Share button → Add to Home Screen
- **Android:** Chrome → three dots → Add to Home screen / Install app

It gets an icon and opens without browser chrome, like any other app.

---

## Step 4 — Save an area before you go

The layer data downloads automatically when you first open it. The topo and
imagery pictures underneath are too big to grab all at once, so you choose.

**At home or at the motel, on wifi:** open the app, pan to the ground you're
headed for, tap **↓**, pick a detail level, tap **Save the area on screen**.
Leave the screen on until it finishes.

Rough sizes for an area a few miles across: "medium" runs 30–80 MB, "maximum
detail" can be several hundred. Start with medium.

Then put the phone in airplane mode and check it still draws. If it does,
you're good.

---

## Using it

**◎** centers on your GPS. Works offline — GPS doesn't need a signal.

**≡** opens layers. Switch between topo and imagery, turn layers on and off,
and slide the fill strength on geology and land manager so you can see the
topo underneath.

**↓** is offline saving and shows how much you've stored.

**Tap any polygon** for its details. Geology gives you the full unit name,
rock type, lithology, and the source citation — not just the abbreviation.
Claims give you name, serial number, type, claimant, and a plain-language note
about how well that particular claim is actually located.

---

## The thing to understand about claim outlines

BLM records claims down to the affected quarter sections. That's all the law
requires them to store, so a claim polygon here is a survey-grid box the claim
falls inside, not the claim itself. The staked corners live in the Notice of
Location in the case file at the BLM state office.

The map is honest about this per claim. BLM scores how well each one mapped, and
the popup translates that score: whether the outline is a direct survey-grid
match, an estimate, or just "somewhere in this square mile."

**On the ground, the posted corner monuments are the boundary.** If the phone
disagrees with a post, the post wins.

---

## Where the data comes from

| Layer | Source |
|---|---|
| Topo and imagery | USGS The National Map |
| Geology | Oregon DOGAMI, Oregon Geologic Data Compilation |
| Mining claims | BLM Mineral and Land Records System |
| Land manager | BLM Surface Management Agency |
| Survey grid | BLM PLSS CadNSDI |

All public domain, pulled directly from the agencies. Nothing is scraped from
any other map site.

The geology colors are DOGAMI's own, read from their published service legend,
so the map looks like the state geologic map rather than something invented.

Two notes on the sources. The geology and claims endpoints are confirmed working.
The land manager and survey grid endpoints are the standard BLM addresses but
were not tested end to end — if either comes back empty or errors, `--check` will
say so, and the layer numbers at the end of those URLs are the usual thing to
adjust.

---

## If something breaks

**Layers say "Not downloaded yet"** — `fetch.py` hasn't run, or ran from a
different folder. Make sure `data/` sits beside `index.html`.

**Map is blank white** — `vendor/` is missing. Re-run `fetch.py`.

**Works at home, blank in the field** — you didn't save tiles for that area, or
you saved them in a browser tab rather than the installed app. Save from inside
the installed app.

**Changed a file but the phone shows the old one** — open `sw.js`, add one to
`SHELL_VERSION`, upload again, then close and reopen the app twice.

---

## License

The code is yours to do anything with — MIT, CC0, whatever you like. The data
belongs to the public. If you hand this to anyone, pass along the note about
claim outlines with it.
