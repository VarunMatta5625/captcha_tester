"""A local stand-in for the login page, so the README visuals never touch a real site or account.

The browser is started with every request blocked except https://login.gitam.edu/* and
https://gstudent.gitam.edu/* , which are answered from this file. The page is deliberately plain and unbranded.
It has the element ids content.js looks for (imgCaptcha, txtCaptchaInput, txtusername, password, Submit,
lblmessage) and checks the captcha against the true label, so the shipped extension runs unchanged.

Captchas come from data/captchas.zip (gold ids, true label known). Used only by make_visuals.py.
"""
import csv, io, os, sys, time
from urllib.parse import parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import prep  # noqa: E402

# gold captchas the shipped model reads with confidence > 0.91 (so the demo is not about a lucky or unlucky pick)
CONFIDENT_IDS = ['1841', '2836', '4322', '4770', '5065', '8152', '8256', '9666', '9699', '10519', '10545', '11956', '13200', '15120', '15689', '16312', '18317', '19184', '19263', '22346', '24101', '24245', '24824', '25044', '25506', '28632', '28676', '28897', '28945', '29060']
DEMO_USER, DEMO_PASSWORD = "demo1234", "demo-password"   # obviously fake; the mock accepts only these

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Campus sign-in (local mock)</title>
<style>
 body{font:15px/1.4 system-ui,sans-serif;background:#eef1f5;margin:0;color:#1f2937}
 .bar{background:#1f3a5f;color:#fff;padding:14px 28px;font-weight:600;letter-spacing:.3px}
 .card{width:380px;margin:36px auto;background:#fff;border-radius:10px;padding:24px 28px;box-shadow:0 2px 14px #0002}
 h1{font-size:19px;margin:0 0 14px} label{display:block;font-weight:600;margin:10px 0 4px}
 input[type=text],input[type=password]{width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #c5ccd6;border-radius:6px;font-size:15px}
 .cap{display:flex;align-items:center;gap:10px;margin-top:6px}.cap img{width:150px;height:45px;border:1px solid #c5ccd6;border-radius:4px}
 .cap a{font-size:13px;color:#1f5fbf;cursor:pointer}
 button{margin-top:16px;width:100%;padding:10px;border:0;border-radius:6px;background:#1f5fbf;color:#fff;font-size:15px;font-weight:600;cursor:pointer}
 #lblmessage{color:#b91c1c;font-weight:600;min-height:20px;margin-top:10px}
 .mock{text-align:center;font-size:12px;color:#6b7280;margin-top:-18px}
</style></head><body>
<div class="bar">Campus portal &middot; local mock for documentation</div>
<form class="card" method="post" action="/Login.aspx" id="form1">
 <h1>Student sign-in</h1>
 <label for="txtusername">User ID</label><input type="text" id="txtusername" name="txtusername" maxlength="16" autocomplete="off">
 <label for="password">Password</label><input type="password" id="password" name="password" maxlength="20" autocomplete="off">
 <label for="txtCaptchaInput">Captcha</label>
 <div class="cap"><img id="imgCaptcha" width="150" height="45" alt="captcha" src="/Captcha.ashx?n=0">
  <a id="refresh" onclick="document.getElementById('imgCaptcha').src='/Captcha.ashx?n='+Date.now()">Refresh</a></div>
 <input type="text" id="txtCaptchaInput" name="txtCaptchaInput" maxlength="5" autocomplete="off" style="margin-top:8px">
 <div id="lblmessage">__MESSAGE__</div>
 <button type="submit" id="Submit" name="Submit">LOGIN</button>
</form></body></html>"""

PORTAL = """<!doctype html><html><head><meta charset="utf-8"><title>Portal home (local mock)</title>
<style>body{font:16px system-ui;background:#eef1f5;margin:0}.bar{background:#1f3a5f;color:#fff;padding:14px 28px;font-weight:600}
.card{width:420px;margin:60px auto;background:#fff;border-radius:10px;padding:28px;box-shadow:0 2px 14px #0002;text-align:center}
a{color:#1f5fbf}</style></head><body><div class="bar">Campus portal &middot; local mock for documentation</div>
<div class="card" id="ok"><h2>You are signed in</h2><p>Demo user <b>demo1234</b></p>
<p><a id="logout" href="https://gstudent.gitam.edu/Home/Logout">Log out</a></p></div></body></html>"""


def redirect_to(url):
    """A page that sends the browser on (meta refresh). Real 3xx answers are avoided on purpose: the browser would
    follow them outside this mock, to the real site."""
    return f'<!doctype html><meta http-equiv="refresh" content="0;url={url}"><title>Redirecting</title>'


class Mock:
    def __init__(self, ids=None, reject_first=0, delay=0.0):
        self.delay = delay            # seconds a captcha image takes to arrive (so "still loading" can be shown)
        gold = {r["id"]: r["label"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "gold.csv")))}
        self.pool = [(i, gold[i]) for i in (ids or CONFIDENT_IDS)]
        self.k = 0
        self.served = []             # ids of the captchas sent so far, in order
        self.current = None          # (id, label) of the captcha last served
        self.reject_first = reject_first   # answer "Invalid CAPTCHA" to this many submits, even for right answers
        self.on_post = None          # optional callback(page) run just before the answer to a login press
        self.submits = []            # (user, password-ok, captcha, accepted)
        self.log = []

    def captcha_png(self):
        i, label = self.pool[self.k % len(self.pool)]
        self.k += 1
        self.current = (i, label)
        self.served.append(i)
        buf = io.BytesIO()
        prep.open_captcha(i).convert("RGB").save(buf, "PNG")
        return buf.getvalue()

    def page(self, message=""):
        return PAGE.replace("__MESSAGE__", message)

    def handle(self, route):
        req = route.request
        url = req.url
        if url.startswith("chrome-extension://"):   # the extension's own pages and files
            return route.continue_()
        host = url.split("/")[2]
        path = "/" + url.split("/", 3)[3] if url.count("/") >= 3 else "/"
        self.log.append((req.method, url))
        if host == "gstudent.gitam.edu":   # the mock portal: home page, and a logout that redirects to the login page
            if path.startswith("/Home/Logout"):
                return route.fulfill(status=200, content_type="text/html", body=redirect_to("https://login.gitam.edu/Login.aspx"))
            return route.fulfill(status=200, content_type="text/html", body=PORTAL)
        if host != "login.gitam.edu":
            return route.abort()
        if path.startswith("/Captcha.ashx"):
            if self.delay:
                time.sleep(self.delay)
            return route.fulfill(status=200, content_type="image/png", body=self.captcha_png(),
                                 headers={"Cache-Control": "no-store"})
        if req.method == "POST":
            form = {k: v[0] for k, v in parse_qs(req.post_data or "").items()}
            user, pw, cap = form.get("txtusername", ""), form.get("password", ""), form.get("txtCaptchaInput", "")
            truth = self.current[1] if self.current else ""
            cap_ok = cap == truth and len(self.submits) >= self.reject_first
            self.submits.append((user, pw == DEMO_PASSWORD, cap, cap_ok))
            if self.on_post:
                self.on_post(req.frame.page)
            if not (user == DEMO_USER and pw == DEMO_PASSWORD):
                return route.fulfill(status=200, content_type="text/html", body=self.page("Invalid User ID or password."))
            if not cap_ok:
                return route.fulfill(status=200, content_type="text/html", body=self.page("Invalid CAPTCHA"))
            return route.fulfill(status=200, content_type="text/html", body=redirect_to("https://gstudent.gitam.edu/Home/Index"))
        return route.fulfill(status=200, content_type="text/html", body=self.page())
