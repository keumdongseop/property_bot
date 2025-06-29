// Korean-English chemical name translator
const chemicalTranslations = {
    // Common chemicals
    '물': 'water',
    '에탄올': 'ethanol',
    '메탄올': 'methanol',
    '아세톤': 'acetone',
    '벤젠': 'benzene',
    '톨루엔': 'toluene',
    '헥산': 'hexane',
    '옥탄': 'octane',
    '질소': 'nitrogen',
    '산소': 'oxygen',
    '이산화탄소': 'carbon dioxide',
    '암모니아': 'ammonia',
    '수소': 'hydrogen',
    '헬륨': 'helium',
    '아르곤': 'argon',
    '메탄': 'methane',
    '에탄': 'ethane',
    '프로판': 'propane',
    '부탄': 'butane',
    '펜탄': 'pentane',
    '에틸렌': 'ethylene',
    '프로필렌': 'propylene',
    '아세틸렌': 'acetylene',
    '황산': 'sulfuric acid',
    '염산': 'hydrochloric acid',
    '염화나트륨': 'sodium chloride',
    '소금': 'sodium chloride',
    
    // Additional chemicals
    '알코올': 'ethanol',  // Common term for alcohol
    '메틸알코올': 'methanol',
    '에틸알코올': 'ethanol',
    '이소프로판올': 'isopropanol',
    '글리세롤': 'glycerol',
    '포름알데히드': 'formaldehyde',
    '아세트알데히드': 'acetaldehyde',
    '아세트산': 'acetic acid',
    '초산': 'acetic acid',
    '개미산': 'formic acid',
    '시트르산': 'citric acid',
    '글루코스': 'glucose',
    '포도당': 'glucose',
    '자당': 'sucrose',
    '설탕': 'sucrose',
    '과산화수소': 'hydrogen peroxide',
    '요소': 'urea',
    '글리콜': 'ethylene glycol',
    '페놀': 'phenol',
    '나프탈렌': 'naphthalene',
    '안트라센': 'anthracene'
};

// Property translations
const propertyTranslations = {
    '밀도': 'density',
    '점도': 'viscosity',
    '점성': 'viscosity',
    '열용량': 'heat_capacity',
    '비열': 'heat_capacity',
    '증기압': 'vapor_pressure',
    '엔탈피': 'enthalpy',
    '엔트로피': 'entropy',
    '깁스에너지': 'gibbs_energy',
    '깁스자유에너지': 'gibbs_energy',
    '헬름홀츠에너지': 'helmholtz_energy',
    '내부에너지': 'internal_energy',
    '열전도도': 'thermal_conductivity',
    '열전도율': 'thermal_conductivity',
    '표면장력': 'surface_tension',
    '임계온도': 'critical_temperature',
    '임계압력': 'critical_pressure',
    '끓는점': 'boiling_point',
    '비점': 'boiling_point',
    '녹는점': 'melting_point',
    '융점': 'melting_point',
    '분자량': 'molecular_weight',
    '몰질량': 'molecular_weight',
    '증발열': 'heat_vaporization',
    '기화열': 'heat_vaporization'
};

// Temperature pattern matching
const temperaturePatterns = [
    /(\d+\.?\d*)\s*도/g,  // 25도
    /(\d+\.?\d*)\s*℃/g,   // 25℃
    /(\d+\.?\d*)\s*°C/g,   // 25°C
    /섭씨\s*(\d+\.?\d*)/g, // 섭씨 25
];

// Translate Korean query to English
function translateQuery(koreanQuery) {
    let translatedQuery = koreanQuery;
    
    // Translate chemical names
    for (const [korean, english] of Object.entries(chemicalTranslations)) {
        const regex = new RegExp(korean, 'gi');
        translatedQuery = translatedQuery.replace(regex, english);
    }
    
    // Translate property names
    for (const [korean, english] of Object.entries(propertyTranslations)) {
        const regex = new RegExp(korean, 'gi');
        translatedQuery = translatedQuery.replace(regex, english);
    }
    
    // Normalize temperature expressions
    for (const pattern of temperaturePatterns) {
        translatedQuery = translatedQuery.replace(pattern, '$1°C');
    }
    
    // Common Korean query patterns to English
    translatedQuery = translatedQuery
        .replace(/의\s+(.+?)(?:는|은|이|가)?\s*(?:얼마|뭐|무엇)?/g, ' $1 of')
        .replace(/에서/g, ' at')
        .replace(/일때/g, ' at')
        .replace(/계산/g, 'calculate')
        .replace(/구하/g, 'calculate')
        .replace(/알려/g, 'tell me')
        .replace(/(?:은|는|이|가)\s*(?:얼마|뭐|무엇)/g, '')
        .replace(/\?/g, '?');
    
    return translatedQuery;
}

// Translate property names back to Korean for display
function translatePropertyToKorean(property) {
    const reverseMap = {
        'density': '밀도',
        'viscosity': '점도',
        'heat_capacity': '열용량',
        'vapor_pressure': '증기압',
        'enthalpy': '엔탈피',
        'entropy': '엔트로피',
        'gibbs_energy': '깁스 자유 에너지',
        'helmholtz_energy': '헬름홀츠 에너지',
        'internal_energy': '내부 에너지',
        'thermal_conductivity': '열전도도',
        'surface_tension': '표면장력',
        'critical_temperature': '임계온도',
        'critical_pressure': '임계압력',
        'boiling_point': '끓는점',
        'melting_point': '녹는점',
        'molecular_weight': '분자량',
        'heat_vaporization': '증발열'
    };
    
    return reverseMap[property] || property;
}

// Translate phase to Korean
function translatePhaseToKorean(phase) {
    const phaseMap = {
        'g': '기체',
        'gas': '기체',
        'l': '액체',
        'liquid': '액체',
        's': '고체',
        'solid': '고체'
    };
    
    return phaseMap[phase] || phase;
}

module.exports = {
    translateQuery,
    translatePropertyToKorean,
    translatePhaseToKorean,
    chemicalTranslations,
    propertyTranslations
};