import pandas as pd
import requests
from bs4 import BeautifulSoup

"""
Some inspection on the html output is needed in order to scrape it.
"""


def scrape_mushroom_table(url: str) -> pd.DataFrame:
    base_url = url.split("/")[0]

    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table", class_="MsoNormalTable")

    data = []
    rows = table.find_all("tr")

    # we can skip the header row
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) == 3:
            # from quick inspection on the html
            col1 = cells[0].get_text(strip=True)  # the latin name
            col2 = cells[1].get_text(
                strip=True
            )  # the link to the website entry (including more info & pics)
            col3 = cells[2].get_text(strip=True)  # the name in german

            link_elem = cells[1].find("a")
            link = f"{base_url}/{link_elem.get('href')}" if link_elem else None

            data.append(
                {
                    "latin_name": col1,
                    "german_link_text": col2,
                    "german_link_url": link,
                    "family_german": col3,
                }
            )

    df = pd.DataFrame(data)

    # we don't need to keep navigational rows (where cols 2 and 3 are empty)
    df_filtered = df[
        (df["german_link_text"].str.strip() != "")
        & (df["family_german"].str.strip() != "")
    ].copy()

    return df_filtered
