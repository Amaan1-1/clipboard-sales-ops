import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://analyst-assessment-production.up.railway.app"
COMMUNITIES_URL = f"{BASE_URL}/communities"


def get_soup(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_community_urls():
    """Discover all community page URLs across all directory pages."""
    urls = set()
    page_url = COMMUNITIES_URL

    while page_url:
        soup = get_soup(page_url)

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if href.startswith("/communities/"):
                urls.add(urljoin(BASE_URL, href))

        next_link = None

        for link in soup.find_all("a", href=True):
            if link.get_text(" ", strip=True).lower() == "next →":
                next_link = urljoin(BASE_URL, link["href"])
                break

        page_url = next_link

    return sorted(urls)


def parse_community(url):
    """Extract facility information from an individual community page."""
    soup = get_soup(url)

    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    def value_after(label):
        try:
            index = lines.index(label)
            return lines[index + 1]
        except (ValueError, IndexError):
            return ""

    name = soup.find("h1").get_text(" ", strip=True)

    address_index = lines.index("Address")
    address_lines = lines[address_index + 1:address_index + 3]

    street = address_lines[0]
    city_state_zip = address_lines[1]

    parts = city_state_zip.rsplit(" ", 2)

    city = parts[0].rstrip(",")
    state = parts[1]
    zip_code = parts[2]

    care_index = lines.index("Care Offerings")
    care_offerings = []

    for line in lines[care_index + 1:]:
        if line in {"Administrator", "Phone", "← Back to all communities"}:
            break
        care_offerings.append(line)

    return {
        "name": name,
        "street": street,
        "city": city,
        "state": state,
        "zip": zip_code,
        "care_offerings": care_offerings,
        "url": url,
    }


def scrape_communities():
    """Scrape every Bellhaven community."""
    urls = get_community_urls()

    communities = []

    for url in urls:
        try:
            community = parse_community(url)
            communities.append(community)
        except Exception as exc:
            print(f"Failed to scrape {url}: {exc}")

    return communities


if __name__ == "__main__":
    communities = scrape_communities()

    print(f"Found {len(communities)} communities.\n")

    for community in communities:
        print(
            f"{community['name']} | "
            f"{community['city']}, {community['state']} "
            f"{community['zip']} | "
            f"{', '.join(community['care_offerings'])}"
        )