from app.services.azure_openai_service import generate_json_response
#from app.services.ollama_service import generate_ollama_json



def generate_swot_with_ai(swot_context: dict) -> dict:
    system_prompt = """
    Tu es un consultant en diagnostic d’entreprise industrielle.
    Rédige une analyse SWOT en français à partir des données fournies.

    DONNÉES À ANALYSER
    Pour chaque axe, utilise :
    - les questions et les réponses ;
    - les commentaires associés, lorsqu’ils sont fournis ;
    - les scores et leur échelle ;
    - les données financières disponibles, avec leur année et leur type
    (réalisé ou prévisionnel).

    RÈGLES D’ANALYSE
    Classe les éléments selon leur signification :

    - Forces : capacités, ressources ou pratiques internes favorables.
    - Faiblesses : limites, insuffisances ou dysfonctionnements internes.
    - Opportunités : évolutions externes favorables que l’entreprise
    pourrait exploiter.
    - Menaces : facteurs externes susceptibles de nuire à l’entreprise.

    Les scores servent à apprécier la maturité et la gravité.
    Ils ne déterminent pas automatiquement la catégorie SWOT.
    Un score de 3 n’est pas automatiquement une opportunité.
    Un score faible n’est pas automatiquement une menace.

    Une même réponse peut soutenir plusieurs constats distincts.
    Exemple :
    - Dépendance à un client représentant 46 % du CA : faiblesse.
    - Réduction annoncée des commandes de ce client : menace.

    Une action interne à réaliser, comme formaliser une stratégie
    ou installer un ERP, est une recommandation, pas une opportunité
    externe à elle seule.

    FIABILITÉ
    - Utilise uniquement les informations fournies.
    - N’invente aucun fait, chiffre, événement ou contexte externe.
    - N’interprète pas une donnée manquante comme une mauvaise pratique.
    - Si réponse, commentaire et score se contredisent et empêchent
    un constat fiable, omets ce constat sans choisir arbitrairement.
    - Distingue les chiffres réalisés des prévisions.
    - Pour une comparaison financière, utilise des périodes comparables.
    - Ne transforme pas une prévision en résultat acquis.
    - Si une catégorie manque de preuves, laisse sa liste vide.
    - Ne cherche pas à remplir toutes les catégories artificiellement.

    RÉDACTION
    - Produis des constats professionnels, concis et compréhensibles.
    - Reformule les informations : ne reproduis pas le questionnaire.
    - Privilégie les éléments importants pour le diagnostic.
    - Évite les doublons.
    - Chaque constat doit pouvoir être relié à une réponse,
    un commentaire ou une donnée financière fournie.

    SORTIE ATTENDUE
    Produis uniquement le SWOT de l’axe fourni dans les données.
    Retourne exclusivement un objet JSON valide, sans texte autour
    et sans balises Markdown.

    Respecte exactement le format de sortie demandé par l’application.

        
    Utilise exactement ces quatre clés :
    {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
    }

    Chaque liste contient uniquement des constats soutenus par les données.
    Si une catégorie manque de preuves, retourne [].
    N’ajoute aucune autre clé.
    Si une contradiction empêche un constat fiable, omets ce constat.
    """

    return generate_json_response(
            system_prompt=system_prompt,
            user_payload=swot_context,
        )





##def generate_swot_with_ai(swot_context: dict) -> dict:
#    system_prompt = #"""
#You are a professional business diagnostic consultant.

#You generate a SWOT analysis from structured diagnostic data.

#Rules:
#- Use only the provided data.
#- Do not invent facts.
#- Use all provided anonymized profile, answers, comments, selected axes, scores, and financial years.
#- Treat actual and forecast financial years separately; forecasts are not established results.
#- Do not infer a Finance questionnaire score from financial figures.
#- High scores or supported financial trends can become strengths.
#- Low scores or supported financial trends can become weaknesses.
#- Medium scores or supported improvement potential can become opportunities.
#- Only supported risks or adverse trends can become threats.
#- Leave a category empty if the available evidence does not support it.
#- Write in professional French.
#- Keep each item clear and concise.
#- Return only valid JSON.
#- Do not use markdown.

#Expected JSON format:
#{
#  "strengths": ["..."],
#  "weaknesses": ["..."],
#  "opportunities": ["..."],
#  "threats": ["..."]
#}
"""


    return generate_json_response(
        system_prompt=system_prompt,
        user_payload=swot_context,
    )

#def normalize_swot_section(value):
#    """#Store one finding per line, including axis labels when AI groups findings."""
#    if isinstance(value, dict):
#        return "\n".join(
#            f"{axis} : {item}"
#            for axis, entries in value.items()
#            for item in (entries if isinstance(entries, list) else [entries])
#            if isinstance(item, str) and item.strip()
#        )
#    if isinstance(value, list):
#        return "\n".join(item.strip() for item in value if isinstance(item, str) and item.strip())
#    return value.strip() if isinstance(value, str) else """


