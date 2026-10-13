class ProviderScoreEngine:

    def choose_best(self, results):

        if not results:
            return None

        best_score = -1
        best_result = None

        for result in results:

            score = 0

            # =========================
            # Competition
            # =========================

            score += result.get(
                "competition_index",
                0
            ) * 0.20

            # =========================
            # Reviews
            # =========================

            score += min(
                result.get(
                    "average_reviews",
                    0
                ) / 100,
                30
            )

            # =========================
            # Rating
            # =========================

            score += result.get(
                "average_rating",
                0
            ) * 8

            # =========================
            # Market Depth
            # =========================

            score += result.get(
                "market_depth",
                0
            ) * 0.30

            result["provider_score"] = round(
                score,
                1
            )

            if score > best_score:

                best_score = score
                best_result = result

        return best_result