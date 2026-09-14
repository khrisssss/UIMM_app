# def generate_fake_swot_from_context(swot_context: dict) -> dict:
#     company = swot_context.get("company", {})
#     company_profile_answers = swot_context.get("company_profile_answers", [])
#     axis_scores = swot_context.get("axis_scores", [])
#     diagnostic_questions = swot_context.get("diagnostic_questions", [])

#     strengths = []
#     weaknesses = []
#     opportunities = []
#     threats = []

#     regulatory_constraints = company.get("specific_regulatory_constraints")
#     general_comment = company.get("general_comment")

#     # -----------------------------
#     # Company profile context
#     # -----------------------------


#     if regulatory_constraints:
#         threats.append(
#             f"Des contraintes réglementaires spécifiques ont été identifiées: {regulatory_constraints}."
#         )

#     if general_comment:
#         opportunities.append(
#             f"Commentaire général à prendre en compte : {general_comment}."
#         )

    
#     # -----------------------------
#     # Axis scores
#     # -----------------------------

#     for score in axis_scores:
#         axis_name = score.get("axis_name")
#         percentage = score.get("score_percentage")

#         if percentage is None:
#             continue

#         if percentage >= 75:
#             strengths.append(
#                 f"{axis_name} constitue un axe prioritaire d'amélioration avec un score de {percentage}%."
#             )
#         elif percentage < 50:
#             weaknesses.append(
#                 f"{axis_name} constitue un axe prioritaire d'amélioration avec un score de {percentage}%."
#             )
#         else:
#             opportunities.append(
#                 f"{axis_name} présente un potentiel d'amélioration avec un score intermédiare de {percentage}% ."
#             )

#     # -----------------------------
#     # Diagnostic answers and comments
#     # -----------------------------

#     for question in diagnostic_questions:
#         axis_name = question.get("axis_name")
#         question_text = question.get("question_text")
#         score_value = question.get("score_value")
#         score_label = question.get("score_label")
#         comment = question.get("comment")

#         if score_value is None:
#             continue

#         if score_value >= 4:
#             strengths.append(
#                 f"{axis_name}: strong result on '{question_text}' ({score_label})."
#             )
#         elif score_value <= 2:
#             weaknesses.append(
#                 f"{axis_name}: improvement needed on '{question_text}' ({score_label})."
#             )

#         if comment:
#             opportunities.append(
#                 f"{axis_name}: consultant comment — {comment}"
#             )

#         opportunity_hint = question.get("opportunity_hint")
#         threat_hint = question.get("threat_hint")

#         if opportunity_hint:
#             opportunities.append(opportunity_hint)

#         if threat_hint:
#             threats.append(threat_hint)

#     # -----------------------------
#     # Fallbacks if empty
#     # -----------------------------

#     if not strengths:
#         strengths.append("No clear strengths identified yet. More diagnostic answers are needed.")

#     if not weaknesses:
#         weaknesses.append("No major weaknesses identified yet from the available answers.")

#     if not opportunities:
#         opportunities.append("Additional opportunities can be identified after completing more diagnostic answers.")

#     if not threats:
#         threats.append("No major threats identified yet from the available answers.")

#     return {
#         "strengths": "\n".join(f"- {item}" for item in strengths),
#         "weaknesses": "\n".join(f"- {item}" for item in weaknesses),
#         "opportunities": "\n".join(f"- {item}" for item in opportunities),
#         "threats": "\n".join(f"- {item}" for item in threats),
#     }




