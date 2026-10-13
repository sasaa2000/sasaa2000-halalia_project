from backend.ranking.score_calculator import ScoreCalculator


class RankingEngine:

    @staticmethod
    def rank(products):

        ranked = []

        for product in products:

            score = ScoreCalculator.calculate(product)

            product["score"] = round(
                score.final_score,
                2
            )

            ranked.append(product)

        ranked.sort(

            key=lambda x: x["score"],

            reverse=True

        )

        return ranked