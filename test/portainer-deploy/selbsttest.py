"""Selbsttest für den Webhook-Schritt von portainer-deploy.yml gegen einen nachgebauten Webhook auf localhost.

Aufruf: python3 -I selbsttest.py <portainer-deploy.yml>
"""
import http.server
import os
import subprocess
import sys
import textwrap
import threading
import unittest

BAUSTEIN = sys.argv.pop(1) if len(sys.argv) > 1 else ".github/workflows/portainer-deploy.yml"


def schritt_laden(name):
    zeilen = open(BAUSTEIN, encoding="utf-8").read().splitlines()
    kopf = next(i for i, z in enumerate(zeilen) if z.strip() == f"- name: {name}")
    start = next(i for i in range(kopf, len(zeilen)) if zeilen[i].strip() == "run: |") + 1
    tiefe = len(zeilen[start]) - len(zeilen[start].lstrip())
    ende = next((i for i in range(start, len(zeilen)) if zeilen[i].strip() and len(zeilen[i]) - len(zeilen[i].lstrip()) < tiefe), len(zeilen))
    return textwrap.dedent("\n".join(zeilen[start:ende]))


SKRIPT = schritt_laden("Webhook auslösen")


class Webhook(http.server.BaseHTTPRequestHandler):
    antworten = []
    anfragen = 0

    def do_POST(self):
        Webhook.anfragen += 1
        code = Webhook.antworten.pop(0) if Webhook.antworten else 204
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *_):
        pass


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Webhook)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def lauf(self, antworten, versuche="20"):
        Webhook.antworten, Webhook.anfragen = list(antworten), 0
        env = dict(os.environ, WEBHOOK=f"http://127.0.0.1:{self.server.server_port}/", WEBHOOK_PAUSE="0", WEBHOOK_VERSUCHE=versuche)
        r = subprocess.run(["bash", "-e", "-c", SKRIPT], env=env, capture_output=True, text=True, timeout=60)
        return r.returncode, Webhook.anfragen, r.stdout + r.stderr

    def test_angenommen(self):
        code, n, _ = self.lauf([204])
        self.assertEqual((code, n), (0, 1))

    def test_409_wird_wiederholt(self):
        code, n, aus = self.lauf([409, 409, 204])
        self.assertEqual((code, n), (0, 3), aus)

    def test_409_bis_zum_ende_scheitert(self):
        code, n, aus = self.lauf([409] * 5, versuche="3")
        self.assertEqual((code, n), (1, 3), aus)
        self.assertIn("HTTP 409", aus)

    def test_anderer_fehler_ohne_wiederholung(self):
        code, n, aus = self.lauf([403])
        self.assertEqual((code, n), (1, 1), aus)
        self.assertIn("HTTP 403", aus)

    def test_ohne_webhook_nichts_ausgerollt(self):
        r = subprocess.run(["bash", "-e", "-c", SKRIPT], env=dict(os.environ, WEBHOOK=""), capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Secret webhook fehlt", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
