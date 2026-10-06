"""Maintainer utility to refresh the vendored frontend; not needed to run the app."""

import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "app" / "static" / "vendor"
ASSETS = {
    "bootstrap.min.css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css",
    "bootstrap.bundle.min.js": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js",
    "bootstrap-icons.css": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/bootstrap-icons.min.css",
    "fonts/bootstrap-icons.woff2": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/fonts/bootstrap-icons.woff2",
    "fonts/bootstrap-icons.woff": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/font/fonts/bootstrap-icons.woff",
    "chart.umd.js": "https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.js",
    "LICENSE-bootstrap": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/LICENSE",
    "LICENSE-bootstrap-icons": "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.1/LICENSE",
    "LICENSE-chartjs": "https://cdn.jsdelivr.net/npm/chart.js@4.5.1/LICENSE.md",
    "LICENSE-manrope": "https://raw.githubusercontent.com/google/fonts/main/ofl/manrope/OFL.txt",
}


def download(url):
    request = Request(url, headers={"User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    )})
    with urlopen(request, timeout=45) as response:
        return response.read()


def main():
    for filename, url in ASSETS.items():
        path = DESTINATION / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        content = download(url)
        if filename.endswith((".js", ".css")):
            # Source maps are for vendor debugging and aren't used in this repository.
            content = re.sub(rb"/\*[#@] sourceMappingURL=.*?\*/", b"", content)
            content = re.sub(rb"//# sourceMappingURL=[^\r\n]*", b"", content)
        path.write_bytes(content)
        print(f"Vendored {filename}")
    css = download("https://fonts.googleapis.com/css2?family=Manrope:wght@200..800&display=swap").decode()
    font_url = re.findall(r"url\((https://[^)]+)\)", css)[-1]
    (DESTINATION / "fonts" / "manrope-latin.woff2").write_bytes(download(font_url))
    print("Vendored Manrope (Latin, variable weights).")


if __name__ == "__main__":
    main()
