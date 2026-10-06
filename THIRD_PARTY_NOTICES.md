# Third-party assets

The app serves these vendored assets from `app/static/vendor/` without network requests.
Their original copyright notices are preserved in the assets and adjacent license files.

| Asset | Version | Upstream | License |
| --- | --- | --- | --- |
| Bootstrap | 5.3.8 | https://github.com/twbs/bootstrap | MIT (`LICENSE-bootstrap`) |
| Bootstrap Icons | 1.13.1 | https://github.com/twbs/icons | MIT (`LICENSE-bootstrap-icons`) |
| Chart.js | 4.5.1 | https://github.com/chartjs/Chart.js | MIT (`LICENSE-chartjs`) |
| Manrope (Latin variable font) | Google Fonts distribution | https://github.com/google/fonts/tree/main/ofl/manrope | SIL Open Font License 1.1 (`LICENSE-manrope`) |

`scripts/fetch_frontend_assets.py` documents and refreshes the upstream assets. It is a
maintainer utility and is never run by the web application. Python dependencies retain
their respective licenses; see their package distributions.
