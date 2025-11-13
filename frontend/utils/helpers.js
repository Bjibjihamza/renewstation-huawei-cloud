// src/utils/helpers.js
// Helper functions pour gérer les données PostgreSQL

/**
 * Convertit une valeur en nombre et applique toFixed
 * Gère les strings, nombres, null, undefined
 * @param {any} value - Valeur à convertir
 * @param {number} decimals - Nombre de décimales (défaut: 1)
 * @returns {string} - Nombre formaté
 */
export const safeToFixed = (value, decimals = 1) => {
  const num = parseFloat(value);
  return isNaN(num) ? '0.0' : num.toFixed(decimals);
};

/**
 * Convertit une valeur en nombre
 * @param {any} value - Valeur à convertir
 * @param {number} fallback - Valeur par défaut si conversion échoue
 * @returns {number}
 */
export const safeParseFloat = (value, fallback = 0) => {
  const num = parseFloat(value);
  return isNaN(num) ? fallback : num;
};

/**
 * Formate un nombre avec séparateurs de milliers
 * @param {any} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales
 * @returns {string}
 */
export const formatNumber = (value, decimals = 0) => {
  const num = safeParseFloat(value);
  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(num);
};

/**
 * Formate une valeur en kW ou W selon la taille
 * @param {any} value - Valeur en W
 * @returns {string}
 */
export const formatPower = (value) => {
  const watts = safeParseFloat(value);
  if (watts >= 1000) {
    return `${(watts / 1000).toFixed(1)} kW`;
  }
  return `${Math.round(watts)} W`;
};

/**
 * Formate une date ISO en format lisible
 * @param {string} isoDate - Date ISO
 * @returns {string}
 */
export const formatDate = (isoDate) => {
  if (!isoDate) return 'N/A';
  try {
    return new Date(isoDate).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return 'Date invalide';
  }
};

/**
 * Calcule le pourcentage entre deux valeurs
 * @param {any} value - Valeur actuelle
 * @param {any} total - Valeur totale
 * @returns {number}
 */
export const calcPercentage = (value, total) => {
  const val = safeParseFloat(value);
  const tot = safeParseFloat(total);
  if (tot === 0) return 0;
  return (val / tot) * 100;
};

/**
 * Filtre les données par date
 * @param {Array} data - Tableau de données
 * @param {string} dateField - Nom du champ date
 * @param {Date} targetDate - Date cible
 * @returns {Array}
 */
export const filterByDate = (data, dateField, targetDate) => {
  const target = targetDate.toISOString().split('T')[0];
  return data.filter(item => 
    item[dateField]?.startsWith(target)
  );
};

/**
 * Regroupe les données par jour de la semaine
 * @param {Array} data - Tableau de données
 * @param {string} dateField - Nom du champ date
 * @param {string} valueField - Nom du champ valeur
 * @returns {Array} - 7 éléments (Lun-Dim)
 */
export const groupByWeekday = (data, dateField, valueField) => {
  const days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
  const grouped = Array(7).fill(0);
  
  data.forEach(item => {
    const date = new Date(item[dateField]);
    const dayIndex = (date.getDay() + 6) % 7; // Lundi = 0
    grouped[dayIndex] += safeParseFloat(item[valueField]);
  });
  
  return days.map((day, idx) => ({
    day,
    value: grouped[idx]
  }));
};