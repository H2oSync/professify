/* =================================================================================================
   termchamp.com/s  —  the link preview for a shared schedule
   Netlify Edge Function. Deno runtime, no dependencies.

   WHY A FUNCTION AND NOT A STATIC FILE
   iMessage, WhatsApp, Slack and Discord read <meta property="og:*"> WITHOUT running JavaScript.
   The app is one static index.html, and a query string does not change which file Netlify serves —
   so every shared schedule previewed with the same generic card, and no amount of client-side code
   could ever change that. This file is the smallest thing that can: it reads the share's image id
   out of the URL and writes it into the meta tags, then hands the human straight on to the app.

   WHAT IT DOES NOT DO
   It does not render the picture. The browser drew that from the student's real sections and
   uploaded it before the link was shared; this only points at it.
   ================================================================================================= */

/* The project URL, with the environment variable as an override rather than a requirement.
   It is not a secret — index.html ships it to every browser in PROFESSIFY_CONFIG — and making
   this function depend on a Netlify env var meant one more manual step between deploying and
   the preview actually working, with a silent fallback to the generic card if it was missed. */
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "https://rqkndeqbcahozidniesn.supabase.co";
const BUCKET       = "schedule-cards";
const FALLBACK_IMG = "https://termchamp.com/share-card.png";

/* The image id comes out of a URL a stranger can craft, so it is matched against a shape rather
   than trusted: 16-64 lowercase hex/dash characters and a .png. That keeps og:image inside this
   one public bucket — it cannot be pointed at another host, another bucket, or a path traversal. */
const ID_RE = /^[a-z0-9-]{16,64}\.png$/;

function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));
}

export default async (request: Request): Promise<Response> => {
  const url = new URL(request.url);
  const id  = url.searchParams.get("i") ?? "";
  const who = (url.searchParams.get("nm") ?? "").slice(0, 40);
  const term= (url.searchParams.get("tm") ?? "").slice(0, 24);
  /* A shared PLAN (the phone app, 2026-09-30) carries pl=A|B|C. Anything else is ignored. */
  const plan = /^[ABC]$/.test(url.searchParams.get("pl") ?? "") ? (url.searchParams.get("pl") as string) : "";
  /* A shared PROFESSOR or CLASS (the phone app, 2026-10-04) carries k=p|c and p=<name slug> or c=<code>.
     Both are matched against a shape: they only ever become ?p= / ?c= for the app, never markup. */
  const kind = url.searchParams.get("k") === "p" ? "p" : url.searchParams.get("k") === "c" ? "c" : "";
  const prof = (url.searchParams.get("p") ?? "").toLowerCase();
  const cls  = (url.searchParams.get("c") ?? "").toUpperCase().replace(/\s+/g, " ").trim();
  const thing = kind === "p" && /^[a-z0-9-]{2,80}$/.test(prof) ? "p" : kind === "c" && /^[A-Z]{2,5} \d{3,4}[A-Z]?$/.test(cls) ? "c" : "";

  const image = (ID_RE.test(id) && SUPABASE_URL)
    ? `${SUPABASE_URL.replace(/\/+$/, "")}/storage/v1/object/public/${BUCKET}/${id}`
    : FALLBACK_IMG;

  /* iMessage renders the card as: image, then og:title in bold, then the domain. It does not show
     og:description at all, so the title has to carry the whole message by itself. */
  const first = who.trim().split(/\s+/)[0] ?? "";
  const title = thing
    ? `${first || "Someone"} shared ${thing === "p" ? "a professor" : "a class"}`
    : plan
    ? (first ? `Look at ${first}'s Plan ${plan}` : `Look at my Plan ${plan}`)
    : (first ? `Look at ${first}'s schedule this semester` : "Look at my schedule this semester");
  const desc  = thing === "p"
    ? "Their rating and the classes they teach, on TermChamp."
    : thing === "c"
    ? "Its sections, professors and seats, on TermChamp."
    : plan
    ? (term ? `Their ${term} Plan ${plan}, and whether yours line up.` : `Their Plan ${plan}, and whether yours line up.`)
    : term
    ? `Their ${term} classes, and whether yours line up.`
    : "See their classes, and whether yours line up.";

  /* Everything except the image id is carried through to the app, which already knows how to open
     a shared schedule from ?sched=. Rebuilding the query from the parameters we recognise — rather
     than forwarding the whole string — means a crafted link cannot use this page to inject
     arbitrary parameters into the app. */
  const onward = new URLSearchParams();
  /* `i` is forwarded now: since 2026-08-29 the shared week lives in the bucket under the same id
     as this picture, rather than base64'd into a ~900-character ?sched= (which is what Tate
     screenshotted). The app reads ?i= and fetches it. ?sched= stays in this list because every
     link sent before that date still carries its own payload and must keep opening. */
  for (const k of ["i", "sched", "nm", "add"]) {
    const v = url.searchParams.get(k);
    if (v) onward.set(k, v);
  }
  /* a professor or class goes to that page: the phone app on a phone, the website's own ?p= / ?c= elsewhere */
  const thingQ = thing === "p" ? "p=" + encodeURIComponent(prof) : thing === "c" ? "c=" + encodeURIComponent(cls) : "";
  const go = thing ? "/?" + thingQ : "/" + (onward.toString() ? "?" + onward.toString() : "");
  const goApp = thing ? "/app/?" + thingQ : "";
  const imgH = thing ? 630 : 1200;
  const imgAlt = thing === "p" ? "A professor and their rating." : thing === "c" ? "A class and who teaches it." : "A week of classes with times and professors.";

  const html = `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<!-- One person's link to one other person. The homepage is what gets indexed. -->
<meta name="robots" content="noindex, follow">
<meta property="og:type"         content="website">
<meta property="og:site_name"    content="TermChamp">
<meta property="og:url"          content="${esc(url.origin + url.pathname + url.search)}">
<meta property="og:title"        content="${esc(title)}">
<meta property="og:description"  content="${esc(desc)}">
<meta property="og:image"        content="${esc(image)}">
<meta property="og:image:width"  content="1200">
<meta property="og:image:height" content="${imgH}">
<meta property="og:image:type"   content="image/png">
<meta property="og:image:alt"    content="${esc(imgAlt)}">
<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
<meta name="twitter:image"       content="${esc(image)}">
<style>
  :root{color-scheme:light dark}
  html,body{height:100%}
  body{margin:0;display:flex;align-items:center;justify-content:center;
    font:500 15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
    background:#154734;color:#F6F4F1;text-align:center;padding:24px}
  .w{max-width:24rem;display:flex;flex-direction:column;align-items:center;gap:14px}
  .logo{width:46px;height:46px;border-radius:13px;background:#5FD3A0;color:#0C2C1F;
    display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800}
  h1{margin:0;font-size:19px;font-weight:700;letter-spacing:-.015em}
  p{margin:0;font-size:14px;color:rgba(246,244,241,.72)}
  a{display:inline-block;margin-top:4px;padding:11px 22px;border-radius:999px;
    background:#5FD3A0;color:#0C2C1F;font-weight:700;text-decoration:none;font-size:15px}
  a:focus-visible{outline:3px solid #F6F4F1;outline-offset:2px}
</style>
</head><body>
  <!-- The no-JavaScript floor. With JS on nobody sees it for longer than a frame. -->
  <div class="w">
    <div class="logo" aria-hidden="true">P</div>
    <h1>${esc(title)}</h1>
    <p>${esc(desc)}</p>
    <a id="go" href="${esc(go)}"${goApp ? ` data-app="${esc(goApp)}"` : ""}>Open in TermChamp</a>
  </div>
<script>
(function(){
  /* Inside an IFRAME — a preview pane, an in-app browser card — "/" is not this app, it is
     whatever that host serves at its own root. Redirecting there hangs on a spinner and makes a
     page that is fine in production look broken. (Learned on /invite, 2026-08-27.) */
  var framed=false;
  try{ framed=(window.top!==window.self); }catch(e){ framed=true; }
  var a=document.getElementById('go');
  if(framed){ if(a)a.setAttribute('target','_top'); return; }
  /* a phone opens a shared professor or class in the phone app */
  var app=a&&a.getAttribute('data-app');
  if(app&&/iPhone|iPod|Android.+Mobile|Mobile.+Safari/i.test(navigator.userAgent||'')) a.setAttribute('href',app);
  /* replace(), not assign(): Back should return to the message, not bounce forward again. */
  try{ location.replace(a.getAttribute('href')); }catch(e){ location.href=a.getAttribute('href'); }
})();
</script>
</body></html>`;

  return new Response(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      /* Apple caches a preview hard per URL, and every share has its own id, so a short public
         cache is safe and keeps the crawler off the origin for repeat fetches of one link. */
      "cache-control": "public, max-age=300",
      "x-robots-tag": "noindex",
    },
  });
};

export const config = { path: "/s" };
