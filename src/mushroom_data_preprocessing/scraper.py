"""
Some inspection on the html output is needed in order to scrape it.
In the future this might be extended to be more flexible (e.g. other website sources)
"""

import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


def retrieve_base_url(url: str) -> str:
    """
    Helper function to retrieve the base url component since this site
    makes quite a lot of use of relative links.
    args:
        url: the url of the page we're currently looking at
    returns:
        base_url
    """
    return "/".join(url.split("/")[:-1])


def scrape_mushroom_table(url: str) -> pd.DataFrame:
    """
    Scrapes the alphabetical index. Assumes a particular structure.
    args:
        url: url of the page
    returns:
        dataframe containing the alphabetical index data
    """
    base_url = retrieve_base_url(url)

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


def remove_non_ascii(string: str) -> str:
    """
    Helper function to remove any non-ascii characters from a string
    by converting str -> bytes -> str.
    """
    return string.encode("ascii", errors="ignore").decode()


def remove_punctuation(string: str) -> str:
    """
    Helper function to remove any punctuation that was added.
    """
    return re.sub(r"[^\w\s]", "", string)


def retrieve_name_and_edibility(list_soup: list[Tag]) -> tuple[str, str]:
    """
    Given a list of <p> elems, extract the mushroom edibility status. With inspection,
    this can be found by searching for the linked edibility data page.
    args:
        list_soup: a list of bs4 parsed <p> objects from the original page
    returns:
        string edibility category for mushroom
        string german name
    """

    edibility = ""
    name = ""

    for soup in list_soup:
        # search for edibility link
        if soup.find_all("a", href="2006Essbarkeit.htm"):
            # this text section contains among other things edibility information
            # name, edibility = determine_name_and_edibility(text_section)
            split_text = soup.get_text().replace("\xa0", " ").split(" ")
            index_edibility = [i for i, item in enumerate(split_text) if item.isupper()][
                0
            ]

            edibility = remove_punctuation(split_text[index_edibility])
            name = " ".join(split_text[0:index_edibility]).strip()
            break

    return edibility, name


def retrieve_characteristics_table(list_soup: list[Tag]) -> dict[str, str]:
    characteristics = {}

    for table in list_soup:
        # this is the characteristics table iff we see "Eigenschaften"
        header_cell = table.find("td")
        if header_cell and "Eigenschaften" in header_cell.get_text():
            rows = table.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    # first cell is the characteristic name
                    # second is the value
                    # not all entries have the exact same set of characteristics
                    # some mushrooms have more info than others
                    key = clean_text(cells[0].get_text()) or ""
                    value = clean_text(cells[1].get_text()) or ""
                    characteristics[key] = value
            break

    return characteristics


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip())
    text = text.rstrip(":")
    return text


def extract_images(soup: BeautifulSoup) -> None:
    pass


def scrape_individual_mushroom_page(
    url: str, base_url: str | None = None
) -> tuple[dict, BeautifulSoup]:
    """
    Scrapes an individual page with particular structure. Assumes a particular structure.
    args:
        url: url of the page
        base_url: a base_url that can help us to resolve relative links
    returns:
        dictionary containing extracted data for that page
    """
    if not base_url:
        base_url = retrieve_base_url(url)

    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, "html.parser")
    all_text_sections = soup.find_all("p")
    all_tables = soup.find_all("table", class_="MsoNormalTable")
    metadata = {}

    metadata["edibility"], metadata["name"] = retrieve_name_and_edibility(
        all_text_sections
    )
    metadata["characteristics"] = retrieve_characteristics_table(all_tables)

    return metadata, soup

    # try:
    #     response = requests.get(url)
    #     soup = BeautifulSoup(response.content, 'html.parser')
