"""Selbsttest für play-upload.yml ohne Google-Konto.

Nimmt das Skript wörtlich aus dem Baustein und lässt es gegen einen
nachgebauten Play-Server auf localhost laufen; der Schlüssel des Dienstkontos
wird für den Lauf neu erzeugt. Aufruf: python3 -I selbsttest.py <play-upload.yml>
"""
import base64
import http.server
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import types
import unittest
import urllib.parse

BAUSTEIN = sys.argv.pop(1) if len(sys.argv) > 1 else ".github/workflows/play-upload.yml"


def skript_laden():
    zeilen = open(BAUSTEIN, encoding="utf-8").read().splitlines()
    start = next(i for i, z in enumerate(zeilen) if "<<'PYEOF'" in z) + 1
    ende = next(i for i in range(start, len(zeilen)) if zeilen[i].strip() == "PYEOF")
    modul = types.ModuleType("play_upload")
    exec(compile(textwrap.dedent("\n".join(zeilen[start:ende])), BAUSTEIN, "exec"), modul.__dict__)
    return modul


P = skript_laden()


class Server(http.server.BaseHTTPRequestHandler):
    """Antwortet wie die Play-API; `fehler` legt je Pfadteil Statuscodes fest, die zuerst kommen."""

    anfragen = []
    fehler = {}

    def log_message(self, *args):
        pass

    def antworten(self, status, inhalt=None):
        daten = json.dumps(inhalt).encode() if inhalt is not None else b""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(daten)))
        self.end_headers()
        self.wfile.write(daten)

    def bearbeiten(self):
        laenge = int(self.headers.get("Content-Length") or 0)
        rumpf = self.rfile.read(laenge) if laenge else b""
        Server.anfragen.append((self.command, self.path, rumpf, self.headers.get("Authorization")))
        for teil, codes in Server.fehler.items():
            if teil in self.path and codes:
                return self.antworten(codes.pop(0), {"error": {"message": "nachgestellt"}})
        if self.path == "/token":
            return self.antworten(200, {"access_token": "probe-token"})
        if self.command == "POST" and self.path.endswith("/edits"):
            return self.antworten(200, {"id": "e1"})
        if "/bundles" in self.path:
            return self.antworten(200, {"versionCode": 4711})
        if self.command == "PUT":
            return self.antworten(200, json.loads(rumpf))
        return self.antworten(200, {} if self.command != "DELETE" else None)

    do_GET = do_POST = do_PUT = do_DELETE = bearbeiten


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Server)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        basis = f"http://127.0.0.1:{cls.server.server_port}"
        P.API, P.UP, P.PAUSE = f"{basis}/api", f"{basis}/up", 0
        cls.tmp = tempfile.mkdtemp()
        cls.schluessel = os.path.join(cls.tmp, "key.pem")
        subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
                        "-out", cls.schluessel], check=True, capture_output=True)
        with open(cls.schluessel) as f:
            konto = {"client_email": "probe@example.iam.gserviceaccount.com",
                     "private_key": f.read(), "token_uri": f"{basis}/token"}
        cls.konto_b64 = base64.b64encode(json.dumps(konto).encode()).decode()
        cls.aab_ordner = os.path.join(cls.tmp, "aab")
        os.makedirs(os.path.join(cls.aab_ordner, "release"))
        with open(os.path.join(cls.aab_ordner, "release", "app-release.aab"), "wb") as f:
            f.write(b"PK\x03\x04probe")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Server.anfragen.clear()
        Server.fehler.clear()
        self.ausgabe = os.path.join(self.tmp, "output")
        open(self.ausgabe, "w").close()

    def lauf(self, **werte):
        env = {"PAKET": "de.example.app", "TRACKS": "internal", "ANTEIL": "", "STATUS": "", "SPRACHE": "de-DE",
               "NOTIZEN_TEXT": "Neu: Probe", "NOTIZEN_DATEI": "", "DRY_RUN": "false", "NUR_PRUEFEN": "false",
               "ARTEFAKT": "aab", "DIENSTKONTO": self.konto_b64, "AAB_ORDNER": self.aab_ordner,
               "GITHUB_OUTPUT": self.ausgabe, "GITHUB_WORKSPACE": self.tmp}
        env.update(werte)
        alt = dict(os.environ)
        os.environ.clear()
        os.environ.update(env)
        try:
            return P.main()
        finally:
            os.environ.clear()
            os.environ.update(alt)

    def folge(self):
        return [(m, p.replace("/api/de.example.app", "").replace("/up/de.example.app", "UP")) for m, p, _, _ in Server.anfragen]

    # Eingaben

    def test_tracks_bereinigt_und_ohne_doppelte(self):
        self.assertEqual(P.tracks_lesen(" internal , alpha,internal "), ["internal", "alpha"])

    def test_unbekannter_track(self):
        with self.assertRaisesRegex(P.Eingabefehler, "Unbekannter Track 'alhpa'"):
            P.tracks_lesen("internal,alhpa")

    def test_ohne_track(self):
        with self.assertRaises(P.Eingabefehler):
            P.tracks_lesen(" , ")

    def test_anteil(self):
        self.assertEqual(P.anteil_lesen(""), 0.1)
        self.assertEqual(P.anteil_lesen("0,5"), 0.5)
        self.assertEqual(P.anteil_lesen("1"), 1.0)
        for falsch in ("0", "1.5", "-0.1", "zehn"):
            with self.assertRaises(P.Eingabefehler, msg=falsch):
                P.anteil_lesen(falsch)

    def test_status_paket_sprache(self):
        self.assertEqual(P.status_lesen(""), "completed")
        for falsch, leser in (("halted", P.status_lesen), ("de.x/../y", P.paket_lesen), ("app", P.paket_lesen),
                              ("deutsch", P.sprache_lesen)):
            with self.assertRaises(P.Eingabefehler, msg=falsch):
                leser(falsch)

    def test_release_staffelung(self):
        r = lambda t, a=0.1, s="completed", n="x": P.release_fuer(t, 7, n, a, s, "de-DE")["releases"][0]
        self.assertEqual(r("internal"), {"status": "completed", "versionCodes": ["7"],
                                         "releaseNotes": [{"language": "de-DE", "text": "x"}]})
        self.assertEqual((r("production")["status"], r("production")["userFraction"]), ("inProgress", 0.1))
        self.assertEqual(r("production", a=0.25)["userFraction"], 0.25)
        self.assertNotIn("userFraction", r("production", a=1))
        self.assertEqual(r("production", a=1)["status"], "completed")
        self.assertEqual(r("production", s="draft"), {"status": "draft", "versionCodes": ["7"],
                                                      "releaseNotes": [{"language": "de-DE", "text": "x"}]})
        self.assertNotIn("releaseNotes", r("alpha", n=""))

    def test_neuigkeiten_laenge(self):
        self.assertEqual(len(P.notizen_lesen("ä" * 500, "")), 500)
        with self.assertRaisesRegex(P.Eingabefehler, "501 Zeichen"):
            P.notizen_lesen("ä" * 501, "")

    def test_neuigkeiten_aus_datei(self):
        with open(os.path.join(self.tmp, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("  Aus der Datei\n")
        os.environ["GITHUB_WORKSPACE"] = self.tmp
        self.assertEqual(P.notizen_lesen("", "notes.txt"), "Aus der Datei")
        with self.assertRaisesRegex(P.Eingabefehler, "fehlt"):
            P.notizen_lesen("", "gibtsnicht.txt")
        with self.assertRaisesRegex(P.Eingabefehler, "Nur eins"):
            P.notizen_lesen("Text", "notes.txt")

    # Abläufe gegen den nachgebauten Server

    def test_nur_pruefen_ohne_netz_und_schluessel(self):
        self.assertEqual(self.lauf(NUR_PRUEFEN="true", DIENSTKONTO="", ARTEFAKT="", TRACKS="internal,production"), 0)
        self.assertEqual(Server.anfragen, [])

    def test_zu_lange_neuigkeiten_legen_keine_bearbeitung_an(self):
        self.assertEqual(self.lauf(NOTIZEN_TEXT="x" * 501), 1)
        self.assertEqual(Server.anfragen, [])

    def test_unbekannter_track_vor_jedem_netzzugriff(self):
        self.assertEqual(self.lauf(TRACKS="internal, alhpa"), 1)
        self.assertEqual(Server.anfragen, [])

    def test_ohne_dienstkonto(self):
        self.assertEqual(self.lauf(DIENSTKONTO=""), 1)
        self.assertEqual(self.lauf(DIENSTKONTO="kein-json"), 1)
        self.assertEqual(Server.anfragen, [])

    def test_dry_run_verwirft_die_bearbeitung(self):
        self.assertEqual(self.lauf(DRY_RUN="true", TRACKS="internal,alpha"), 0)
        self.assertEqual(self.folge(), [
            ("POST", "/token"), ("POST", "/edits"), ("POST", "UP/edits/e1/bundles?uploadType=media"),
            ("PUT", "/edits/e1/tracks/internal"), ("PUT", "/edits/e1/tracks/alpha"),
            ("POST", "/edits/e1:validate"), ("DELETE", "/edits/e1")])
        with open(self.ausgabe) as f:
            self.assertIn("version-code=4711", f.read())

    def test_commit_mit_staffelung(self):
        self.assertEqual(self.lauf(TRACKS="internal,production", ANTEIL="0.2"), 0)
        folge = self.folge()
        self.assertEqual(folge[-1], ("POST", "/edits/e1:commit"))
        self.assertNotIn(("DELETE", "/edits/e1"), folge)
        puts = {p.rsplit("/", 1)[1]: json.loads(r)["releases"][0] for m, p, r, _ in Server.anfragen if m == "PUT"}
        self.assertEqual(puts["internal"]["status"], "completed")
        self.assertEqual((puts["production"]["status"], puts["production"]["userFraction"]), ("inProgress", 0.2))
        self.assertEqual(puts["production"]["releaseNotes"], [{"language": "de-DE", "text": "Neu: Probe"}])
        self.assertTrue(all(a == "Bearer probe-token" for _, p, _, a in Server.anfragen if p != "/token"))

    def test_jwt_ist_mit_dem_schluessel_signiert(self):
        self.assertEqual(self.lauf(DRY_RUN="true"), 0)
        rumpf = urllib.parse.parse_qs(Server.anfragen[0][2].decode())
        self.assertEqual(rumpf["grant_type"], ["urn:ietf:params:oauth:grant-type:jwt-bearer"])
        kopf, inhalt, signatur = rumpf["assertion"][0].split(".")
        roh = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
        self.assertEqual(json.loads(roh(kopf)), {"alg": "RS256", "typ": "JWT"})
        self.assertEqual(json.loads(roh(inhalt))["scope"], "https://www.googleapis.com/auth/androidpublisher")
        oeffentlich = os.path.join(self.tmp, "pub.pem")
        sig = os.path.join(self.tmp, "sig.bin")
        subprocess.run(["openssl", "pkey", "-in", self.schluessel, "-pubout", "-out", oeffentlich], check=True)
        with open(sig, "wb") as f:
            f.write(roh(signatur))
        pruefung = subprocess.run(["openssl", "dgst", "-sha256", "-verify", oeffentlich, "-signature", sig],
                                  input=f"{kopf}.{inhalt}".encode(), capture_output=True)
        self.assertEqual(pruefung.returncode, 0, pruefung.stdout + pruefung.stderr)

    def test_5xx_wird_wiederholt(self):
        Server.fehler["/bundles"] = [503, 500]
        self.assertEqual(self.lauf(DRY_RUN="true"), 0)
        self.assertEqual(sum(1 for m, p in self.folge() if "/bundles" in p), 3)

    def test_dauerhafter_5xx_verwirft_die_bearbeitung(self):
        Server.fehler[":commit"] = [503] * 4
        self.assertEqual(self.lauf(), 1)
        folge = self.folge()
        self.assertEqual(sum(1 for m, p in folge if p.endswith(":commit")), 4)
        self.assertEqual(folge[-1], ("DELETE", "/edits/e1"))

    def test_4xx_wird_nicht_wiederholt_und_verwirft(self):
        Server.fehler["/tracks/internal"] = [403]
        self.assertEqual(self.lauf(), 1)
        folge = self.folge()
        self.assertEqual(sum(1 for m, p in folge if "/tracks/" in p), 1)
        self.assertNotIn(("POST", "/edits/e1:commit"), folge)
        self.assertEqual(folge[-1], ("DELETE", "/edits/e1"))

    def test_genau_ein_bundle(self):
        leer = os.path.join(self.tmp, "leer")
        os.makedirs(leer, exist_ok=True)
        self.assertEqual(self.lauf(AAB_ORDNER=leer), 1)
        self.assertEqual(Server.anfragen, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
