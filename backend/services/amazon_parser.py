from bs4 import BeautifulSoup


class AmazonParser:

    def parse(self, html):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        results = soup.select(
            'div[data-component-type="s-search-result"]'
        )

        prices = []
        ratings = []
        reviews = []

        for item in results[:10]:

            # ----------------------
            # Price
            # ----------------------

            price = item.select_one(
                ".a-price-whole"
            )

            if price:

                try:
                    prices.append(
                        float(
                            price.text.replace(",", "")
                        )
                    )
                except:
                    pass

            # ----------------------
            # Rating
            # ----------------------

            rating = item.select_one(
                ".a-icon-alt"
            )

            if rating:

                try:
                    ratings.append(
                        float(
                            rating.text.split()[0]
                        )
                    )
                except:
                    pass

            # ----------------------
            # Reviews
            # ----------------------

            review = item.select_one(
                ".a-size-base.s-underline-text"
            )

            if review:

                try:
                    reviews.append(
                        int(
                            review.text.replace(",", "")
                        )
                    )
                except:
                    pass

        return {

            "search_results": len(results),

            "average_price":
                round(sum(prices)/len(prices),2)
                if prices else 0,

            "average_rating":
                round(sum(ratings)/len(ratings),2)
                if ratings else 0,

            "average_reviews":
                int(sum(reviews)/len(reviews))
                if reviews else 0,

            "top_seller_reviews":
                max(reviews) if reviews else 0,

            "top_seller_rating":
                max(ratings) if ratings else 0,

            "competition_index":
                min(len(results),100),

            "market_depth":
                min(len(results)*2,100),

            "best_seller":
                len(results) > 50

        }