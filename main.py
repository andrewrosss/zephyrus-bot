# stdlib
import os
import re
import sys
import argparse

# 3rd party
import bs4
import loguru
import requests

# local
# -----


__version__ = "0.1.0"

ROG_ZERPHYRUS_G14_PAGE = "https://www.bestbuy.ca/en-ca/product/14575597"

# other sample products (for testing)
TUF_PAGE = "https://www.bestbuy.ca/en-ca/product/14497496"
DELL_G3_PAGE = "https://www.bestbuy.ca/en-ca/product/13986352"
ACER_NITRO_PAGE = "https://www.bestbuy.ca/en-ca/product/14541215"

# to emulate a browser
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15"
ACCEPT_LANGUAGE = "en,en-US;q=0,5"
ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-language": ACCEPT_LANGUAGE,
    "Accept": ACCEPT,
}

# class used to identify the div which has the availability status
CLASS_LIST = "x-pdp-availability-online onlineAvailabilityContainer_Z02qk"

# if this RegEx matches then we'll say it's available
AVAILABLE_REGEX = re.compile(r"[Aa]vailable")

# the template to use when logging http respoonses
RESPONSE_TEMPLATE = "{status_code} - {reason} - {url}"

# the slack channel to post to
SLACK_WEB_HOOK_URL = os.getenv("SLACK_WEB_HOOK_URL", None)


def configure_logger(level: str = "DEBUG") -> loguru._logger.Logger:
    """Configures the loguru logger obeject."""
    logger = loguru.logger
    logger.remove()
    logger.add(sys.stdout, level=level)
    return logger


logger = configure_logger()


def main(event, context) -> None:
    """The GCF entrypoint."""
    check_availability(ROG_ZERPHYRUS_G14_PAGE)


def cli() -> None:
    """The CLI entrypoint"""
    parser = create_parser()
    args = parser.parse_args()
    _ = configure_logger(args.log_level)
    args.func(args)


def create_parser() -> argparse.ArgumentParser:
    description = "check the availability of a product at the given url."
    parser = argparse.ArgumentParser(description=description)
    parser.set_defaults(func=lambda args: check_availability(args.url))
    parser.add_argument(
        "url",
        nargs="?",
        type=str,
        default=ROG_ZERPHYRUS_G14_PAGE,
        help="The BestBuy product page URL. If not specified, the availability "
        "status of the ASUS ROG Zephyrus G14 is retrieved (url: "
        f"{ROG_ZERPHYRUS_G14_PAGE})",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const="DEBUG",
        default="INFO",
        dest="log_level",
        help="set logging to DEBUG",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
        help="display version info",
    )
    return parser


def check_availability(url: str) -> None:
    """Checks the Whether the BestBuy product at the specified URL is available.

    Args:
        url (str): The product page URL.
    """
    soup = get_product_page(url)

    div = get_availability_div(soup)
    if div is None:
        logger.error(f"Cound not find div with class: {CLASS_LIST}")
        return

    span = get_availability_span(div)
    if span is None:
        logger.error(f"No spans found in div with class: {CLASS_LIST}")
        return

    logger.info(span.text)

    send_response(span.text)


def get_product_page(url: str) -> bs4.BeautifulSoup:
    """Gets and parses the product page retrieved from the specified url.

    Args:
        url (str): The product page URL.

    Raises:
        ValueError: If the request returns a non-2XX status code.

    Returns:
        bs4.BeautifulSoup: The parsed HTML response.
    """
    logger.debug("Retrieving product page")
    r = requests.get(url, headers=HEADERS)
    logger.debug(
        RESPONSE_TEMPLATE, status_code=r.status_code, reason=r.reason, url=r.url
    )
    if r.status_code not in [200, 201, 203]:
        raise ValueError(f"Got unexpected status code: {r.status_code}")
    return bs4.BeautifulSoup(r.text, "html.parser")


def get_availability_div(soup: bs4.BeautifulSoup) -> bs4.element.Tag:
    """Finds the div containing the product availabiltiy.

    Args:
        soup (bs4.BeautifulSoup): The parsed HTML in which to search.

    Returns:
        bs4.element.Tag: The div containing the product availability.
    """
    # find the div that should contain the desired span
    logger.debug("Searching for availability div")
    divs = soup.find_all("div", {"class": CLASS_LIST})
    if len(divs) == 0:
        return None
    return divs[0]


def get_availability_span(div: bs4.element.Tag) -> bs4.element.Tag:
    """Finds the HTML span tag containing the product availability.

    Args:
        div (bs4.element.Tag): The parent element in which to search.

    Returns:
        bs4.element.Tag: The span containing the product availability.
    """
    # find the desired span inside that div
    logger.debug("Searching for availability span")
    spans = div.find_all("span")
    if len(spans) == 0:
        return None
    return spans[-1]


def send_response(text: str) -> None:
    """Sends a message to the slack channel indicated by the SLACK_WEB_HOOK_URL env
    variable.

    Args:
        text (str): The text to send as the message.
    """
    logger.debug("Sending Slack message")
    response_text = f"{text}"
    if AVAILABLE_REGEX.search(text):
        response_text = f":tada: {response_text} :tada:"
    if SLACK_WEB_HOOK_URL is None:
        logger.warning(
            "No Slack URL set. To send a slack message set the SLACK_WEB_HOOK_URL "
            "environment to the desired web hook URL"
        )
    else:
        r = requests.post(SLACK_WEB_HOOK_URL, json={"text": response_text},)
        logger.debug(
            RESPONSE_TEMPLATE, status_code=r.status_code, reason=r.reason, url=r.url
        )


if __name__ == "__main__":
    cli()
