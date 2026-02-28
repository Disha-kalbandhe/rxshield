const axios = require("axios");

const checkDrugInteraction = async (rxcuiList) => {
  try {
    const url = `https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=${rxcuiList.join("+")}`;
    const { data } = await axios.get(url);

    const interactions =
      data.fullInteractionTypeGroup?.[0]?.fullInteractionType || [];

    return interactions.map((interaction) => {
      const pair = interaction.interactionPair[0];
      return {
        drug1: pair.interactionConcept[0].minConceptItem.name,
        drug2: pair.interactionConcept[1].minConceptItem.name,
        severity: pair.severity,
        description: pair.description,
      };
    });
  } catch (err) {
    return [];
  }
};

module.exports = { checkDrugInteraction };
