def generate_fake_swot_from_context(swot_context: dict) -> dict:
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    for question in swot_context["questions"]:
        score_value = question.get("score_value")
        score_code = question.get("score_code")
        theme = question.get("theme")
        comment = question.get("comment")

        if score_code == "SO":
            continue

        if score_value is None:
            continue

        if score_value >= 4:
            strengths.append(
                f"{theme}: {question.get('high_score_meaning')}"
            )

        if score_value <= 2:
            weaknesses.append(
                f"{theme}: {question.get('low_score_meaning')}"
            )

            if question.get("opportunity_hint"):
                opportunities.append(
                    f"{theme}: {question.get('opportunity_hint')}"
                )

            if question.get("threat_hint"):
                threats.append(
                    f"{theme}: {question.get('threat_hint')}"
                )

        if comment:
            # For now, we keep the comment only indirectly.
            # Later, Azure OpenAI will use comments much better.
            pass

    return {
        "strengths": "\n".join(strengths) if strengths else "Aucune force majeure identifiée à ce stade.",
        "weaknesses": "\n".join(weaknesses) if weaknesses else "Aucune faiblesse majeure identifiée à ce stade.",
        "opportunities": "\n".join(opportunities) if opportunities else "Aucune opportunité prioritaire identifiée à ce stade.",
        "threats": "\n".join(threats) if threats else "Aucune menace majeure identifiée à ce stade.",
    }