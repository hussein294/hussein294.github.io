# hussein294.github.io

The personal website of Hussein Mohamed Al-Alfy: AI engineering services, two paid diplomas and free learning material.

The site is static. A small Python script (`build.py`) turns the templates and Markdown files into HTML, and GitHub publishes the result every time you push.

## What is where

| You want to change | Edit this |
|---|---|
| Name, email, phone, profile links, ADA link | `site.yml` |
| Course dates, prices, course text (English and Arabic) | `data/courses.yml` |
| A free-learning post | one Markdown file in `learn/<track>/` |
| The list of free-learning tracks | `data/tracks.yml` |
| Home, Services, Projects, About, Contact | `pages/*.html` |
| Header, footer, page layouts | `templates/*.html` |
| Colours, fonts, spacing | `static/css/site.css` |
| Photo, favicon, link-preview image | `static/img/`, `static/favicon.svg` |

## Publish on GitHub Pages

The repository must be named exactly `hussein294.github.io` and must be public.

### Option A: the GitHub website

1. Sign in to GitHub as `hussein294`. Click **+** → **New repository**.
2. Name it `hussein294.github.io`, choose **Public**, and click **Create repository**.
3. Unzip the site on your computer. On Windows, turn on **View → Show → Hidden items** in File Explorer so you can see the `.github` folder.
4. On the new repository page, click **uploading an existing file**.
5. Open the unzipped folder, select everything inside it (including `.github` and `.gitignore`), and drag it into the browser. Wait until every file is listed.
6. Click **Commit changes**.
7. Go to **Settings → Pages**. Under **Build and deployment**, set **Source** to **GitHub Actions**.
8. Open the **Actions** tab. If no run has started, click **Publish site → Run workflow**.
9. When the run shows a green tick (about a minute), open `https://hussein294.github.io`.

If the `.github` folder did not upload, create the file by hand: **Add file → Create new file**, name it `.github/workflows/deploy.yml`, and paste in the contents of that file from the zip.

### Option B: git

```
cd path\to\unzipped\site
git init -b main
git add .
git commit -m "First version of the site"
git remote add origin https://github.com/hussein294/hussein294.github.io.git
git push -u origin main
```

Then do steps 7 to 9 from Option A.

### Plan B if the workflow fails on launch day

The second zip, `hussein294-site-prebuilt.zip`, holds the finished HTML. Upload its contents to the repository instead, then set **Settings → Pages → Source** to **Deploy from a branch**, branch `main`, folder `/ (root)`. The site goes live without any build step. Switch back to the full repository when you have time.

## Preview on your own computer

You need Python 3.10 or newer.

```
pip install -r requirements.txt
python build.py
python -m http.server 8000 --directory _site
```

Open `http://localhost:8000`. Run `python build.py --drafts` to include posts marked as drafts.

## Add a free-learning post

1. Create a Markdown file in the track's folder, for example `learn/engineering-qa/my-new-post.md`.
2. Start it with this block:

   ```
   ---
   title: "The title of the post"
   description: "One sentence shown in lists and link previews."
   date: 2026-12-01
   track: engineering-qa
   tags: [rag, evaluation]
   draft: true
   ---
   ```

3. Write the post in Markdown below the block. Start sections with `##`.
4. When you are happy with it, change `draft: true` to `draft: false` and push.

Notes:

- A post marked `draft: true` is not published.
- For a numbered series, add `series_order: 9`. Posts in a series get Previous and Next links.
- The file name becomes the address. `learn/engineering-qa/my-new-post.md` is published at `/learn/engineering-qa/my-new-post/`. A leading number such as `09-` is dropped.
- To take a published post down, set `draft: true` and push.

### Add a new track

Add an entry to `data/tracks.yml` with an `id`, `name`, `kind` and `summary`, then create the folder `learn/<id>/`. The track appears on the home page and the Free learning page once it has a published post.

## Update course dates and prices

Open `data/courses.yml`. Each course has these two lines:

```
next_cohort: { en: "", ar: "" }
price: { en: "", ar: "" }
```

Fill in the text exactly as it should appear, in both languages:

```
next_cohort: { en: "1 February 2027", ar: "1 فبراير 2027" }
price: { en: "EGP 0,000", ar: "0,000 جنيه" }
```

While a value is empty, the page shows "To be announced" or "Ask ADA". The `status` line under each language says where the cohort stands; update it when a cohort starts. The registration link for both courses is `ada.url` in `site.yml`.

## Show or hide the phone number

The phone number is off. To show it in the footer and on the Contact page, set `phone` in `site.yml`, for example `phone: "+20 110 001 7365"`. The repository is public, so the number becomes public as soon as you push it.

## Switch on a custom domain later

1. Buy the domain from any registrar.
2. At the registrar, add these DNS records:
   - For `www.yourdomain.com`: a `CNAME` record pointing to `hussein294.github.io`.
   - For the bare `yourdomain.com`: four `A` records pointing to `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and `185.199.111.153`.
3. In the repository, go to **Settings → Pages → Custom domain**, enter the domain and save. Tick **Enforce HTTPS** once GitHub offers it. DNS can take up to a day.
4. In `site.yml`, change `url` to the new address, for example `https://yourdomain.com`, and push. This updates the sitemap, the feed and the link previews.

The old `hussein294.github.io` address redirects to the new domain automatically.

## What the site does not do

- It does not take payments. Course enrolment and payment go through ADA.
- It has no contact form. Contact is by email and profile links, so there is no third-party form service to maintain.
- It loads fonts from Google Fonts. Nothing else is fetched from outside.
