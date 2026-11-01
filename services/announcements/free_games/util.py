class FreeGamesFetcher:
    def __init__(self):
        self.epic_url = (
            "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
            "?locale=en-US&country=US&allowCountries=US"
        )
        self.steam_url = "https://store.steampowered.com/api/featuredcategories?cc=US&l=en"
        self.epic_store_base = "https://store.epicgames.com/en-US/p/"
        self.steam_store_base = "https://store.steampowered.com/app/"

    @staticmethod
    def _active_epic_offer(element):
        promotions = element.get("promotions") or {}
        for offer_window in promotions.get("promotionalOffers") or []:
            for offer in offer_window.get("promotionalOffers") or []:
                discount = offer.get("discountSetting", {}).get("discountPercentage")
                if discount == 0:
                    return offer.get("endDate")
        return None

    def _epic_slug(self, element):
        mappings = element.get("offerMappings") or element.get("catalogNs", {}).get("mappings") or []
        if mappings:
            return mappings[0].get("pageSlug")
        return element.get("productSlug")

    def parse_epic(self, data):
        elements = data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
        games = []
        for element in elements:
            until = self._active_epic_offer(element)
            if until is None:
                continue
            slug = self._epic_slug(element)
            url = f"{self.epic_store_base}{slug}" if slug else "https://store.epicgames.com/en-US/free-games"
            games.append((element.get("id"), element.get("title"), url, until))
        return games

    def parse_steam(self, data):
        specials = (data.get("specials") or {}).get("items") or []
        games = []
        for item in specials:
            if item.get("discount_percent") != 100:
                continue
            app_id = item.get("id")
            games.append((str(app_id), item.get("name"), f"{self.steam_store_base}{app_id}", None))
        return games
