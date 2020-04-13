import re
import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin


class Metadata:
    url = ""
    type = ""  # https://ogp.me/#types
    title = ""
    description = ""
    image = ""

    def __str__(self):
        return (
            "{url: "
            + self.url
            + ", type: "
            + self.type
            + ", title: "
            + self.title
            + ", description: "
            + self.description
            + ", image: "
            + self.image
            + "}"
        )


class Metadatareader:
    @staticmethod
    def get_metadata_from_url_in_text(text):
        # look for the first url in the text
        # and extract the url metadata
        urls_in_text = Metadatareader.get_urls_from_text(text)
        if len(urls_in_text) > 0:
            return Metadatareader.get_url_metadata(urls_in_text[0])
        return Metadata()

    @staticmethod
    def get_urls_from_text(text):
        """Method to look for all URLs in a given text, extract them and return them as a tuple of urls.
        :requires:

        :param text: A valid block of text of any lenght.

        :returns:
        A tuple of valid URLs extracted from the text.
        """
        regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        return re.findall(regex, text)

    @staticmethod
    def get_url_metadata(url):
        """This method looks for the page of a given URL, extracts the page content and parses the content with
        BeautifulSoup searching for the page meta, then it returns the metadata in case there is any.
        :requires:

        :param url: Any valid URL to search for.

        :returns:
        Metadata information extracted from a webpage.
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        metadata = Metadata()
        metadata.url = url
        metadata.type = "website"
        for meta in soup.findAll("meta"):
            # priorize using Open Graph Protocol
            # https://ogp.me/
            metadata.type = Metadatareader.get_meta_property(
                meta, "og:type", metadata.type
            )
            metadata.title = Metadatareader.get_meta_property(
                meta, "og:title", metadata.title
            )
            metadata.description = Metadatareader.get_meta_property(
                meta, "og:description", metadata.description
            )
            metadata.image = Metadatareader.get_meta_property(
                meta, "og:image", metadata.image
            )
            if metadata.image:
                metadata.image = urljoin(url, metadata.image)

        if not metadata.title and soup.title:
            # use page title
            metadata.title = soup.title.text

        if not metadata.image:
            # use first img element
            images = soup.find_all("img")
            if len(images) > 0:
                metadata.image = urljoin(url, images[0].get("src"))

        if not metadata.description and soup.body:
            # use text from body
            for text in soup.body.find_all(string=True):
                if (
                    text.parent.name != "script"
                    and text.parent.name != "style"
                    and not isinstance(text, Comment)
                ):
                    metadata.description += text

        if metadata.description:
            # remove white spaces and break lines
            metadata.description = re.sub("\n|\r|\t", " ", metadata.description)
            metadata.description = re.sub(" +", " ", metadata.description)
            metadata.description = metadata.description.strip()

        return metadata

    @staticmethod
    def get_meta_property(meta, property_name, default_value=""):
        if "property" in meta.attrs and meta.attrs["property"] == property_name:
            return meta.attrs["content"]
        return default_value
