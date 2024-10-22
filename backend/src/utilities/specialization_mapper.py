from typing import List, Dict, Set
from dataclasses import dataclass
from thefuzz import fuzz
from src.config.settings.logger_config import logger

@dataclass
class SpecializationGroup:
    """
    A class to represent a specialization group with its primary name, aliases, and relevant keywords.
    
    Attributes:
    ----------
    primary: str
        The primary name of the specialization (e.g., 'cardiology').
    aliases: Set[str]
        A set of alternative names for the specialization (e.g., 'cardiologist', 'heart specialist').
    keywords: Set[str]
        A set of keywords associated with the specialization (e.g., 'heart', 'cardiovascular').
    """
    primary: str
    aliases: Set[str]
    keywords: Set[str]

class SpecializationMapper:
    """
    A class responsible for mapping medical specializations based on primary names, aliases, and keywords.
    
    Methods:
    -------
    find_matching_specializations(target_specialization: str, similarity_threshold: int = 80) -> List[str]:
        Finds and returns a list of matching specializations based on the target specialization string.
    """
    def __init__(self) -> None:
        """
        Initializes the SpecializationMapper with predefined specialization groups, aliases, and keywords.
        """
        self.specialization_groups: Dict[str, SpecializationGroup] = {
            "cardiology": SpecializationGroup(
                primary="cardiology",
                aliases={"cardiologist", "heart specialist", "heart doctor", "cardiac specialist"},
                keywords={"heart", "cardiac", "cardiovascular", "chest", "heart disease"}
            ),
            "neurology": SpecializationGroup(
                primary="neurology",
                aliases={"neurologist", "brain specialist", "nerve specialist", "brain doctor"},
                keywords={"brain", "nerve", "neural", "nervous system", "headache", "migraine"}
            ),
            "dermatology": SpecializationGroup(
                primary="dermatology",
                aliases={"dermatologist", "skin specialist", "skin doctor"},
                keywords={"skin", "dermal", "cutaneous", "acne", "rash"}
            ),
            "gastroenterology": SpecializationGroup(
                primary="gastroenterology",
                aliases={"gastroenterologist", "digestive specialist", "gi doctor"},
                keywords={"stomach", "digestive", "intestine", "gi tract", "gut"}
            ),
            "orthopedics": SpecializationGroup(
                primary="orthopedics",
                aliases={"orthopedist", "bone specialist", "joint specialist", "orthopedic surgeon"},
                keywords={"bone", "joint", "skeletal", "fracture", "spine"}
            ),
            "pediatrics": SpecializationGroup(
                primary="pediatrics",
                aliases={"pediatrician", "child specialist", "child doctor"},
                keywords={"child", "infant", "baby", "pediatric", "children"}
            ),
            "psychiatry": SpecializationGroup(
                primary="psychiatry",
                aliases={"psychiatrist", "mental health specialist", "mental health doctor"},
                keywords={"mental", "psychiatric", "psychological", "behavior", "mood"}
            ),
            "pulmonology": SpecializationGroup(
                primary="pulmonology",
                aliases={"pulmonologist", "lung specialist", "respiratory doctor"},
                keywords={"lung", "respiratory", "breathing", "pulmonary", "chest"}
            ),
            "endocrinology": SpecializationGroup(
                primary="endocrinology",
                aliases={"endocrinologist", "hormone specialist", "diabetes doctor"},
                keywords={"hormone", "thyroid", "diabetes", "endocrine", "metabolic"}
            ),
            "ophthalmology": SpecializationGroup(
                primary="ophthalmology",
                aliases={"ophthalmologist", "eye specialist", "eye doctor"},
                keywords={"eye", "vision", "ocular", "blurry vision", "eye pain", "eye infection"}
            ),
            "nephrology": SpecializationGroup(
                primary="nephrology",
                aliases={"nephrologist", "kidney specialist", "renal doctor"},
                keywords={"kidney", "renal", "urine", "kidney stones", "renal failure"}
            ),
            "gynecology": SpecializationGroup(
                primary="gynecology",
                aliases={"gynecologist", "women's health specialist", "female health doctor"},
                keywords={"female", "reproductive", "pelvic", "menstrual", "ovarian", "uterus"}
            ),
            "urology": SpecializationGroup(
                primary="urology",
                aliases={"urologist", "urinary tract specialist", "bladder specialist"},
                keywords={"urinary", "bladder", "kidney", "prostate", "urine", "urination problems"}
            ),
            "allergology": SpecializationGroup(
                primary="allergology",
                aliases={"allergist", "allergy specialist", "immune system doctor"},
                keywords={"allergy", "immune", "asthma", "rash", "swelling", "sneezing"}
            ),
            "obstetrics": SpecializationGroup(
                primary="obstetrics",
                aliases={"obstetrician", "pregnancy specialist", "childbirth doctor"},
                keywords={"pregnancy", "childbirth", "labor", "prenatal", "pregnant"}
            ),
        }

        self.alias_to_primary: Dict[str, str] = {}
        for primary, group in self.specialization_groups.items():
            for alias in group.aliases:
                self.alias_to_primary[alias.lower()] = primary
            self.alias_to_primary[primary.lower()] = primary

        # Define terms for general practitioners and non-specialized doctors to exclude
        self.excluded_specializations: Set[str] = {
            "general practitioner", "gp", "general doctor", "mbbs", "general medicine"
        }

    def find_matching_specializations(self, target_specialization: str, similarity_threshold: int = 80) -> List[str]:
        """
        Finds and returns a list of matching specializations based on the target specialization string.
        
        Parameters:
        ----------
        target_specialization : str
            The input specialization term to be matched.
        similarity_threshold : int, optional
            The fuzzy matching threshold for identifying close matches (default is 80).
            
        Returns:
        -------
        List[str]
            A list of matched specialization names and their aliases.
        """
        target_lower = target_specialization.lower()
        matches: Set[str] = set()

        try:
            if target_lower in self.alias_to_primary:
                primary = self.alias_to_primary[target_lower]
                if primary not in self.excluded_specializations:
                    matches.add(primary)
                    matches.update(self.specialization_groups[primary].aliases)

            for primary, group in self.specialization_groups.items():
                if fuzz.ratio(target_lower, primary.lower()) >= similarity_threshold and primary not in self.excluded_specializations:
                    matches.add(primary)
                    matches.update(group.aliases)

                for alias in group.aliases:
                    if fuzz.ratio(target_lower, alias.lower()) >= similarity_threshold and primary not in self.excluded_specializations:
                        matches.add(primary)
                        matches.update(group.aliases)
                        break

                for keyword in group.keywords:
                    if (keyword.lower() in target_lower or target_lower in keyword.lower()) and primary not in self.excluded_specializations:
                        matches.add(primary)
                        matches.update(group.aliases)
                        break

            logger.info(f"Found matching specializations for '{target_specialization}': {matches}")
            return list(matches)

        except Exception as e:
            logger.error(f"Error finding matching specializations: {e}")
            return [target_specialization]
