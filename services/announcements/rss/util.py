from defusedxml import ElementTree as ET


class FeedParser:
    def __init__(self):
        self.atom_ns = "{http://www.w3.org/2005/Atom}"

    @staticmethod
    def _text(element, tag):
        node = element.find(tag)
        return node.text.strip() if node is not None and node.text else ""

    def _parse_atom_entry(self, entry):
        item_id = self._text(entry, f"{self.atom_ns}id")
        title = self._text(entry, f"{self.atom_ns}title")
        link_node = entry.find(f"{self.atom_ns}link")
        link = link_node.get("href", "") if link_node is not None else ""
        published = self._text(entry, f"{self.atom_ns}published")
        return item_id, title, link, published

    def _parse_rss_item(self, item):
        item_id = self._text(item, "guid") or self._text(item, "link")
        title = self._text(item, "title")
        link = self._text(item, "link")
        published = self._text(item, "pubDate")
        return item_id, title, link, published

    def parse_feed(self, xml_text):
        root = ET.fromstring(xml_text)
        entries = root.findall(f"{self.atom_ns}entry")
        if entries:
            return [self._parse_atom_entry(entry) for entry in entries]
        return [self._parse_rss_item(item) for item in root.findall(".//item")]
