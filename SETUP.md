# Sticker-board GitHub profile: setup

## 1. Create the profile repo
Make a **public** repo named exactly like your GitHub username: `ujjal-kumar-roy/ujjal-kumar-roy`.
GitHub shows its `README.md` on your profile page. If you already have that repo, replace its contents with this folder.

## 2. Push these files
This folder lives inside `mv-next-frontend` for safekeeping, but it is published from its own repo. Copy it into a clone of the profile repo and push from there:
```bash
git clone https://github.com/ujjal-kumar-roy/ujjal-kumar-roy.git ~/code/ujjal-kumar-roy
rsync -a --exclude __pycache__ ~/code/fsmb_space/mv-next-frontend/github-profile/ ~/code/ujjal-kumar-roy/
cd ~/code/ujjal-kumar-roy
git add .
git commit -m "feat: sticker-board profile README"
git push
```

## 3. Let the Action write
Repo → **Settings → Actions → General → Workflow permissions** → choose **Read and write permissions** → Save.

Then **Actions → Redraw profile → Run workflow**. In about a minute the README and `assets/` are rebuilt with your real GitHub numbers.
Until that first run, the GitHub activity cards show preview numbers.
After that it runs every night at 06:17 Dhaka time, and again whenever you push a change to `profile.json` or `scripts/`.

## 4. Count private contributions (recommended)
Most company work lives in private repos, and the built-in token only sees public activity. To include it:
1. Create a classic token at https://github.com/settings/tokens with the `read:user` scope.
2. Repo → Settings → Secrets and variables → Actions → **New secret** named `PROFILE_TOKEN`.
3. Turn on "Include private contributions on my profile" in your GitHub profile settings.

## Editing
Everything you see comes from **`profile.json`**. Never edit `README.md` or `assets/` by hand: the next build overwrites them.

| Field | What it changes |
|---|---|
| `display_name`, `initials`, `tagline`, `tags`, `corner` | The hero card. `corner_color` and `corner_dot` style the "Open to work" sticker |
| `links` | Badge row under the hero. `kind` picks the icon: linkedin, mail, globe, code, stack, github |
| `sections` | Every block below the badges, in order. Each has a `type`, an optional `label` + `chip` heading |
| `views_badge`, `footer`, `comment` | Profile-view counter, the keyword line at the bottom, the hidden HTML comment at the top |

Section types:

| `type` | Card |
|---|---|
| `whoami` | Terminal card. `blocks` of `cmd` + `lines`; `arrows` and `bold_first` style the lines |
| `tiles` | Big-number stickers (`value`, `label`, `icon`, `color`), `cols` per row |
| `snapshot` | Key / value sheet (`rows` of `key`, `value`) |
| `cards` | Two-per-row cards (`title`, `status`, `desc`, `impact`, `tags`, `footer`, `url`). `linked: true` makes them clickable |
| `chips` | Tech stack chip board (`groups` of `title`, `note`, `items`) plus an optional `details` table |
| `timeline` | Experience stickers (`company`, `role`, `dates`, `desc`, `tags`) |
| `github` | Stats, 6- and 12-month heatmaps and the 30-day line. `year_toggle` tucks the 12-month map into a `<details>`; `collapsed` hides the whole section in one |
| `repos` | Cards from your pinned repos (falls back to top-starred) |
| `cta` | Contact banner with a stamp, linked to `href`, followed by the badges listed in `links` |

Icons for cards and tiles: calendar, cap, people, bug, bolt, code, layers, payment, shield, pulse, scales, chart, briefcase, trophy, medal, star, sparkle, wheel, cloud, network, pipeline, terminal, repo.
Colours live in `scripts/tokens.json` (light and dark sets).

## Preview locally
```bash
pip install -r scripts/requirements.txt
python scripts/build.py --demo           # fake numbers, no token
GH_TOKEN=ghp_xxx python scripts/build.py # real numbers
```

Fonts: Fredoka and DM Mono, SIL Open Font License (see `scripts/fonts/`). They're embedded in each SVG, so the cards look the same everywhere.
