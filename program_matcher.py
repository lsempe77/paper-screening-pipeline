"""
Program name matcher using explicit variation lists (no LLM inference, no fuzzy matching)
This eliminates LLM hallucination issues with program recognition.

DESIGN DECISION: Explicit variations instead of fuzzy matching
- Fully auditable: Know exactly which variation maps to which program
- Deterministic: Same input always gives same output
- Maintainable: Add variations as discovered
- No false matches: Only matches explicitly listed variations
"""

from typing import Tuple, Optional, Dict, Set
import re

# RELEVANT PROGRAMS: Graduation/ultra-poor programs (cash + productive assets)
# Each key is the canonical program name, values are all known variations
RELEVANT_PROGRAMS: Dict[str, Set[str]] = {
    "BRAC CFPR-TUP": {
        "brac cfpr-tup",
        "brac cfpr",
        "brac tup",
        "brac challenging the frontiers of poverty reduction",
        "cfpr-tup",
        "cfpr tup",
        "brac ultra poor graduation"
    },
    "BRAC SPIR/Shouhardo": {
        "spir",
        "shouhardo",
        "brac spir",
        "brac shouhardo",
        "strengthening household ability to respond to development opportunities"
    },
    "Gaibandha Ultra Poor (GUP)": {
        "gup",
        "gaibandha ultra poor",
        "gaibandha ultra-poor",
        "ultra poor programme gaibandha"
    },
    "Chars Livelihoods Programme (CLP)": {
        "clp",
        "chars livelihoods programme",
        "chars livelihood programme",
        "chars livelihoods program",
        "chars livelihood program"
    },
    "The Hunger Project (THP)": {
        "thp",
        "the hunger project",
        "hunger project",
        "targeting the hardest to reach"
    },
    "IGVGD/Bandhan": {
        "igvgd",
        "bandhan",
        "income generation for vulnerable group development",
        "income generation for vulnerable groups development"
    },
    "Generic Graduation/TUP Programs": {
        "graduation program",
        "graduation programme",
        "tup program",
        "tup programme",
        "targeting the ultra poor",
        "targeting the ultra-poor",
        "ultra poor graduation",
        "ultra-poor graduation"
    },
    "WINGS": {
        "wings",
        "women's income generating support",
        "womens income generating support",
        "wings program",
        "wings programme"
    },
    "Concern Worldwide Graduation": {
        "concern worldwide graduation",
        "concern graduation",
        "concern worldwide tup"
    },
    "LEAP (Ghana)": {
        "leap",
        "livelihood empowerment against poverty",
        "ghana leap",
        "leap ghana"
    },
    "Child Grant Programme (CGP)": {
        "cgp",
        "child grant programme",
        "child grant program"
    },
    "Hunger Safety Net Programme (HSNP)": {
        "hsnp",
        "hunger safety net programme",
        "hunger safety net program",
        "kenya hsnp"
    },
    "Zambia Child Grant (ZCTP)": {
        "zctp",
        "zambia child grant programme",
        "zambia child grant program",
        "zambia cgt"
    },
    "PATH": {
        "path",
        "path jamaica",
        "programme of advancement through health and education",
        "program of advancement through health and education"
    },
    "Productive Safety Net Programme (PSNP)": {
        "psnp",
        "productive safety net programme",
        "productive safety net program",
        "ethiopia psnp",
        "ethiopian productive safety net"
    },
    "Growth Enhancement Support Scheme (GESS)": {
        "gess",
        "growth enhancement support scheme",
        "ges scheme",
        "nigeria gess",
        "growth enhancement support",
        "agricultural input subsidy nigeria"
    }
}

# IRRELEVANT PROGRAMS: Microfinance, pure cash transfers, or other non-matching programs
IRRELEVANT_PROGRAMS: Dict[str, Set[str]] = {
    "Grameen Bank": {
        "grameen bank",
        "grameen"
    },
    "Punjab Rural Support Programme (PRSP)": {
        "prsp",
        "punjab rural support programme",
        "punjab rural support program"
    },
    "Egyptian Social Fund": {
        "egyptian social fund",
        "egyptian sfd",
        "social fund for development egypt"
    },
    "Fadama": {
        "fadama",
        "national fadama development project",
        "fadama project",
        "nigeria fadama"
    },
    "Bolsa Familia": {
        "bolsa familia",
        "bolsa família",
        "brazil bolsa familia"
    },
    "Oportunidades/Progresa": {
        "oportunidades",
        "progresa",
        "prospera",
        "mexico oportunidades"
    },
    "GiveDirectly": {
        "givedirectly",
        "give directly"
    }
}

def normalize_text(text: str) -> str:
    """
    Normalize text for exact matching:
    - Lowercase
    - Remove extra whitespace
    - Remove punctuation except hyphens in program names
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Normalize quotes
    text = text.replace('"', '').replace('"', '').replace('"', '')
    text = text.replace("'", '').replace("'", '').replace("'", '')
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Strip
    text = text.strip()
    
    return text


def extract_program_name_from_text(text: str) -> Optional[str]:
    """
    Extract potential program name from text.
    Looks for patterns like: "evaluates the [PROGRAM]", "impact of [PROGRAM]", etc.
    """
    text_lower = text.lower()
    
    # Common patterns for program mentions
    patterns = [
        r'evaluates? (?:the )?([A-Z][^,\.]{5,}(?:programme|program|project|initiative|fund))',
        r'impact of (?:the )?([A-Z][^,\.]{5,}(?:programme|program|project|initiative|fund))',
        r'([A-Z][^,\.]{5,}(?:programme|program|project|initiative|fund))',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    
    return None


def match_program(program_name_or_text: str, title: str, abstract: str) -> Tuple[str, str]:
    """
    Match program against known relevant/irrelevant programs using EXPLICIT VARIATION LISTS.
    
    Design: Uses explicit variations for each program instead of fuzzy matching.
    - Transparent: Know exactly which variation matched
    - Deterministic: Same input = same output
    - Maintainable: Add variations as discovered
    - No false matches: Only exact variations match
    
    Args:
        program_name_or_text: Program name or text containing program name (from LLM)
        title: Paper title
        abstract: Paper abstract
    
    Returns:
        Tuple of (assessment, reasoning)
        assessment: "YES" (relevant), "NO" (irrelevant), "UNCLEAR" (not in lists)
    """
    
    # Handle empty/unclear responses
    if not program_name_or_text:
        return "UNCLEAR", "No program name provided"
    
    normalized_input = normalize_text(program_name_or_text)
    
    # Check for explicit "unclear" markers
    unclear_markers = ["unclear", "not specified", "n/a", "none", "not identified", 
                       "no specific program", "no program mentioned"]
    if any(marker in normalized_input for marker in unclear_markers):
        return "UNCLEAR", "No specific program identified in text"
    
    # Normalize all search texts
    normalized_title = normalize_text(title)
    normalized_abstract = normalize_text(abstract)
    search_text = f"{normalized_title} {normalized_abstract} {normalized_input}"
    
    # CHECK RELEVANT PROGRAMS
    for canonical_name, variations in RELEVANT_PROGRAMS.items():
        for variation in variations:
            normalized_variation = normalize_text(variation)
            
            # Exact match in any of the texts
            if normalized_variation in search_text:
                return "YES", f"Matched relevant program: {canonical_name} (variation: '{variation}')"
    
    # CHECK IRRELEVANT PROGRAMS
    for canonical_name, variations in IRRELEVANT_PROGRAMS.items():
        for variation in variations:
            normalized_variation = normalize_text(variation)
            
            # Exact match in any of the texts
            if normalized_variation in search_text:
                return "NO", f"Matched irrelevant program: {canonical_name} (variation: '{variation}')"
    
    # NOT IN EITHER LIST
    return "UNCLEAR", f"Program not found in known lists. Extracted text: '{program_name_or_text[:100]}'"


def is_program_in_lists(program_text: str) -> Optional[bool]:
    """
    Quick check if program is in lists without full matching logic.
    
    Returns:
        True: Matched relevant program
        False: Matched irrelevant program  
        None: Not in either list
    """
    if not program_text:
        return None
    
    normalized_text = normalize_text(program_text)
    
    # Check relevant
    for variations in RELEVANT_PROGRAMS.values():
        for variation in variations:
            if normalize_text(variation) in normalized_text:
                return True
    
    # Check irrelevant
    for variations in IRRELEVANT_PROGRAMS.values():
        for variation in variations:
            if normalize_text(variation) in normalized_text:
                return False
    
    return None


def add_program_variation(program_canonical_name: str, new_variation: str, is_relevant: bool = True):
    """
    Helper function to add new program variation to the lists.
    Use this when you discover a program is mentioned with a new name variant.
    
    Args:
        program_canonical_name: The canonical program name (key in dict)
        new_variation: The new variation to add
        is_relevant: True for RELEVANT_PROGRAMS, False for IRRELEVANT_PROGRAMS
    """
    target_dict = RELEVANT_PROGRAMS if is_relevant else IRRELEVANT_PROGRAMS
    
    if program_canonical_name in target_dict:
        target_dict[program_canonical_name].add(new_variation.lower())
        print(f"Added variation '{new_variation}' to {program_canonical_name}")
    else:
        print(f"Warning: {program_canonical_name} not found in {'RELEVANT' if is_relevant else 'IRRELEVANT'}_PROGRAMS")
        print(f"Available programs: {list(target_dict.keys())}")


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("BRAC CFPR-TUP", "Evaluating BRAC's Ultra Poor Graduation Program", "This paper evaluates..."),
        ("Malawi SCTP", "Social Cash Transfer Programme", "Malawi SCTP evaluation..."),
        ("LEAP Ghana", "LEAP program evaluation", "Livelihood Empowerment Against Poverty..."),
    ]
    
    print("Testing Program Matcher with Explicit Variations\n")
    print("=" * 80)
    
    for prog_name, title, abstract in test_cases:
        assessment, reasoning = match_program(prog_name, title, abstract)
        print(f"\nProgram: {prog_name}")
        print(f"Assessment: {assessment}")
        print(f"Reasoning: {reasoning}")
        print("-" * 80)
