// Display labels only: database and API values stay unchanged.
const labels = {
  draft: "Brouillon", validated: "Validé", archived: "Archivé",
  manual: "Saisie manuelle", ai: "Généré par l’IA", azure_openai: "Généré par l’IA",
  openai: "Généré par l’IA", ollama: "Généré par l’IA", fake: "Démonstration",
  admin: "Administrateur", consultant: "Consultant",
  unassessed: "Non évalué", green: "Bon", orange: "À suivre", red: "Attention",
  active: "Actif", inactive: "Inactif", actual: "Réalisé", forecast: "Prévisionnel",
};

export function displayLabel(value) {
  return labels[value] ?? value ?? "—";
}

const errorMessages = {
  "Category not found": "Catégorie introuvable.",
  "Category must belong to the selected axis": "La catégorie doit appartenir à l’axe sélectionné.",
  "Axis not found": "Axe introuvable.",
  "Question not found": "Question introuvable.",
  "ordered_question_ids cannot be empty.": "La liste des questions à réorganiser ne peut pas être vide.",
  "Company not found": "Entreprise introuvable.",
  "Scoring scale not found for this question": "Aucun barème disponible pour cette question.",
  "Invalid score code for this question": "Le score sélectionné n’est pas valide pour cette question.",
  "Invalid username or password": "Identifiant ou mot de passe incorrect.",
  "User account is inactive": "Ce compte utilisateur est désactivé.",
  "No scoring scales found for this axis": "Aucun barème disponible pour cet axe.",
  "Parent category not found": "Catégorie parente introuvable.",
  "Parent category must belong to the same axis": "La catégorie parente doit appartenir au même axe.",
  "A category cannot be its own parent": "Une catégorie ne peut pas être sa propre catégorie parente.",
  "Parent category must belong to the selected axis": "La catégorie parente doit appartenir à l’axe sélectionné.",
  "The reorder list must contain all categories for this group.": "La liste doit contenir toutes les catégories de ce groupe.",
  "Company axis not found": "Axe de l’entreprise introuvable.",
  "This axis is not selected for this company": "Cet axe n’est pas sélectionné pour cette entreprise.",
  "Section not found": "Section introuvable.",
  "Profile question not found": "Question de profil introuvable.",
  "Year and kind must match URL": "L’année et le type doivent correspondre à ceux de la page.",
  "Financial year already exists": "Cette année financière existe déjà pour ce type.",
  "Financial year not found": "Année financière introuvable.",
  "No trained model metrics found. Train the model first.": "Aucun modèle entraîné disponible. Veuillez d’abord entraîner le modèle.",
  "Report not found": "Rapport introuvable.",
  "The report must be saved and validated before generating a PowerPoint.": "Le rapport doit être enregistré et validé avant de générer le PowerPoint.",
  "Scoring scale not found": "Barème introuvable.",
  "Scoring level not found": "Niveau de score introuvable.",
  "This axis already has a scoring scale.": "Cet axe dispose déjà d’un barème.",
  "SWOT not found": "Analyse SWOT introuvable.",
  "Username already exists": "Cet identifiant existe déjà.",
  "Invalid role": "Rôle non valide.",
  "User not found": "Utilisateur introuvable.",
  "You cannot delete your own account while logged in.": "Vous ne pouvez pas supprimer votre propre compte pendant votre connexion.",
  "Not authenticated": "Veuillez vous connecter.",
  "Invalid or expired token": "Votre session a expiré. Veuillez vous reconnecter.",
  "Not enough permissions": "Vous n’avez pas les droits nécessaires pour effectuer cette action."
};

export function translateErrorDetail(detail) {
  if (typeof detail === "string") return errorMessages[detail] ?? detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => ({
      ...item,
      msg: item.type === "missing" ? "Ce champ est obligatoire."
        : item.type?.includes("parsing") ? "La valeur saisie n’est pas valide."
        : item.type?.includes("greater_than") ? "La valeur saisie est trop faible."
        : item.type?.includes("less_than") ? "La valeur saisie est trop élevée."
        : item.type === "string_too_long" ? "Le texte saisi est trop long."
        : item.type === "enum" || item.type === "literal_error" ? "Veuillez choisir une valeur autorisée."
        : "Vérifiez la valeur saisie pour ce champ.",
    }));
  }
  return detail;
}
