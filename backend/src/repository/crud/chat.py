"""
Imports for integrating OpenAI and application configuration settings.

- OpenAI: Client library for interacting with OpenAI's API.
- config_env: Configuration settings for environment variables.
- logger: Application logging configuration for monitoring and debugging.
"""

import re
from queue import Queue
from typing import Any

from openai import OpenAI
from src.config.settings.base import config_env
from src.config.settings.logger_config import logger

client = OpenAI(api_key=config_env.OPENAI_API_KEY)

reminder_queue: Queue[str] = Queue()

SYSTEM_PROMPT = """
You are a knowledgeable healthcare assistant bot. Your role is to assist users with medical-related queries, provide detailed information about health issues, symptoms, and medications, and recommend healthcare professionals when necessary. 
Here's how you should respond:
1. If the user asks a healthcare-related question, provide an accurate and empathetic response based on medical knowledge.
2. If the user's symptoms indicate that they should consult a doctor, recommend a specialist based on the condition (e.g., suggest a cardiologist for heart issues).
3. Provide the name of the specialization clearly in your response when recommending a doctor.
4. If the user's question is unrelated to healthcare, politely inform them that you only assist with medical-related queries.
5. Maintain the context of the conversation and ensure all responses are relevant to ongoing medical queries.
"""

conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]


async def enqueue_reminder(prescription: Any) -> None:
    """
    Enqueue a reminder message for the given prescription.

    Args:
        prescription (Any): The prescription object containing the medication name.
    """
    medication_name = prescription.medication_name
    reminder_message = await generate_reminder_message(medication_name)
    reminder_queue.put(reminder_message)


async def get_chatbot_response(user_message: str) -> dict:
    """
    Fetches the response from OpenAI and checks if a doctor or prescription is needed.
    Now also handles explicit user requests for a doctor or specialist.
    """
    logger.info(f"Fetching response from OpenAI for user message: {user_message}")
    try:
        conversation_history.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        answer = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": answer})
        logger.info(f"Received response from OpenAI: {answer}")

        # First, check if the user explicitly requests a doctor or specialist
        explicit_specialization = extract_specialization_from_user_message(user_message)
        if explicit_specialization is None:
            explicit_specialization = ""
        else:
            explicit_specialization = explicit_specialization.strip()
        if explicit_specialization:
            logger.info(
                f"User explicitly requested a specialist: {explicit_specialization}"
            )
            return {
                "response": answer,
                "suggest_doctor": True,
                "specialization": explicit_specialization,
            }

        # Next, check if the AI response suggests seeing a doctor or if the user's message does
        if needs_doctor(user_message, answer):
            specialization = extract_specialization_from_gpt(answer)
            logger.info(f"Extracted specialization from GPT response: {specialization}")
            return {
                "response": answer,
                "suggest_doctor": True,
                "specialization": specialization,
            }

        # Finally, check if there is a need to check prescriptions
        if needs_prescription_check(user_message, answer):
            logger.info("User message or GPT response suggests checking prescriptions")
            return {
                "response": answer,
                "check_prescriptions": True,
            }

        return {
            "response": answer,
            "suggest_doctor": False,
            "check_prescriptions": False,
        }

    except Exception as e:
        logger.error(f"Failed to fetch response from OpenAI: {e}", exc_info=True)
        raise


def needs_prescription_check(user_message: str, gpt_response: str) -> bool:
    """
    Determines whether a user message or GPT response contains any prescription-related keywords.

    This function checks if any of the following keywords related to prescriptions or medication
    are present in either the user's message or the GPT response:
    ["prescription", "prescriptions", "medication", "medications", "medicine", "drug", "pill", "pills", "refill", "reminder", "reminders"].

    Args:
        user_message (str): The message provided by the user.
        gpt_response (str): The response generated by GPT.

    Returns:
        bool: True if any prescription-related keywords are found in the user message or GPT response, False otherwise.
    """
    prescription_keywords = [
        "prescription",
        "prescriptions",
        "medication",
        "medications",
        "medicine",
        "drug",
        "pill",
        "pills",
        "refill",
        "reminder",
        "reminders",
    ]
    user_message_lower = user_message.lower()
    gpt_response_lower = gpt_response.lower()

    return any(
        keyword in user_message_lower or keyword in gpt_response_lower
        for keyword in prescription_keywords
    )


def extract_specialization_from_gpt(response: str) -> str:
    """
    Extracts a medical specialization based on the symptoms or health issues mentioned in the GPT response.

    This function analyzes the input response to identify specific symptoms and maps them to the appropriate
    medical specialization. It checks for known symptom-to-specialization mappings (e.g., chest pain -> cardiologist).
    If no specific match is found, the function checks for general phrases that suggest consulting a general practitioner.
    If no match is identified, the function returns a message asking for more details.

    Args:
        response (str): The GPT-generated response that may contain symptoms or health-related issues.

    Returns:
        str: The medical specialization that corresponds to the symptoms or a request for more symptom details.
             If a symptom is found in the response, the relevant specialization is returned.
             If no clear symptom is found, a general practitioner specialization is suggested.
             If no match is made, the function asks for more specific details.
    """

    logger.debug(f"Extracting specialization from response: {response}")

    symptom_to_specialization = {
        # Cardiologist-related symptoms
        "chest pain": "cardiologist",
        "shortness of breath": "cardiologist",
        "palpitations": "cardiologist",
        "high blood pressure": "cardiologist",
        # Pulmonologist-related symptoms
        "coughing": "pulmonologist",
        "wheezing": "pulmonologist",
        "asthma": "pulmonologist",
        "bronchitis": "pulmonologist",
        # Neurologist-related symptoms
        "severe headache": "neurologist",
        "migraines": "neurologist",
        "numbness": "neurologist",
        "seizures": "neurologist",
        "memory loss": "neurologist",
        "tingling in extremities": "neurologist",
        # Gastroenterologist-related symptoms
        "abdominal pain": "gastroenterologist",
        "diarrhea": "gastroenterologist",
        "constipation": "gastroenterologist",
        "nausea": "gastroenterologist",
        "heartburn": "gastroenterologist",
        "vomiting": "gastroenterologist",
        "bloody stools": "gastroenterologist",
        # Dermatologist-related symptoms
        "skin rash": "dermatologist",
        "itching": "dermatologist",
        "acne": "dermatologist",
        "psoriasis": "dermatologist",
        "eczema": "dermatologist",
        # Orthopedist-related symptoms
        "back pain": "orthopedist",
        "joint pain": "orthopedist",
        "bone fracture": "orthopedist",
        "arthritis": "orthopedist",
        # Ophthalmologist-related symptoms
        "blurry vision": "ophthalmologist",
        "eye pain": "ophthalmologist",
        "dry eyes": "ophthalmologist",
        "loss of vision": "ophthalmologist",
        "red eyes": "ophthalmologist",
        # Nephrologist-related symptoms
        "kidney pain": "nephrologist",
        "swollen legs": "nephrologist",
        "frequent urination": "nephrologist",
        "blood in urine": "nephrologist",
        # Endocrinologist-related symptoms
        "diabetes": "endocrinologist",
        "thyroid issues": "endocrinologist",
        "unexplained weight loss": "endocrinologist",
        # Psychiatrist-related symptoms
        "anxiety": "psychiatrist",
        "depression": "psychiatrist",
        "panic attacks": "psychiatrist",
        "mood swings": "psychiatrist",
        "insomnia": "psychiatrist",
        # Gynecologist-related symptoms
        "pregnancy": "gynecologist",
        "period pain": "gynecologist",
        "menstrual cramps": "gynecologist",
        "irregular periods": "gynecologist",
        "pelvic pain": "gynecologist",
        # Urologist-related symptoms
        "urinary tract infection": "urologist",
        "difficulty urinating": "urologist",
        "incontinence": "urologist",
        "erectile dysfunction": "urologist",
        # Rheumatologist-related symptoms
        "joint swelling": "rheumatologist",
        "stiffness": "rheumatologist",
        "autoimmune disease": "rheumatologist",
        # Allergist-related symptoms
        "allergies": "allergist",
        "hay fever": "allergist",
        "food allergy": "allergist",
        "sinusitis": "allergist",
        # Obstetrician-related symptoms
        "pregnancy complications": "obstetrician",
        "prenatal care": "obstetrician",
        # General Practitioner symptoms (including previously duplicated keys)
        "fever": "general practitioner",
        "cough": "general practitioner",
        "fatigue": "general practitioner",
        "sore throat": "general practitioner",
        "dizziness": "general practitioner",
    }

    response_lower = response.lower()

    # Step 1: Check for specific symptom-to-specialization matches
    for symptom, specialization in symptom_to_specialization.items():
        if symptom in response_lower:
            logger.debug(
                f"Matched symptom '{symptom}' to specialization '{specialization}'"
            )
            return specialization

    # Step 2: General fallback for phrases indicating "general practitioner"
    general_indicators = [
        (r"you should see a doctor", "general practitioner"),
        (r"consult a medical professional", "general practitioner"),
        (r"visit a healthcare provider", "general practitioner"),
        (r"speak with a physician", "general practitioner"),
        (r"medical attention", "general practitioner"),
        (r"seek professional help", "general practitioner"),
    ]

    for indicator, specialization in general_indicators:
        if re.search(indicator, response_lower):
            logger.debug(f"Found general indicator: {indicator}")
            return specialization

    # Step 3: If unable to determine, ask for more symptoms
    logger.warning("No clear match found. Asking for more information.")
    return "Can you provide more details about your symptoms? For example, is the pain sharp, dull, or radiating to other areas?"


def extract_specialization_from_user_message(user_message: str) -> str:
    """
    Extracts the medical specialization directly from the user's message if explicitly mentioned.

    This function checks the user's message for keywords that correspond to specific medical specializations.
    It looks for terms like "heart doctor", "neurologist", "skin specialist", etc., and returns the related
    specialization. The function supports several common medical fields, such as cardiology, neurology, dermatology,
    and more.

    Args:
        user_message (str): The message provided by the user, which may contain explicit references to medical specializations.

    Returns:
        str: The medical specialization mentioned in the user's message if a keyword match is found.
             Returns None if no specialization is explicitly mentioned.
    """
    specialization_keywords = {
        "cardiologist": ["cardiologist", "heart doctor", "heart specialist"],
        "neurologist": ["neurologist", "brain doctor", "nerve doctor"],
        "pulmonologist": ["pulmonologist", "lung doctor", "respiratory specialist"],
        "gastroenterologist": ["gastroenterologist", "digestive specialist"],
        "dermatologist": ["dermatologist", "skin doctor", "skin specialist"],
        "orthopedist": ["orthopedist", "bone doctor", "joint specialist"],
        "ophthalmologist": ["ophthalmologist", "eye doctor"],
        "nephrologist": ["nephrologist", "kidney doctor"],
        "endocrinologist": ["endocrinologist", "hormone doctor", "diabetes specialist"],
        "psychiatrist": ["psychiatrist", "mental health specialist", "psychologist"],
        "gynecologist": ["gynecologist", "female health doctor"],
        "urologist": ["urologist", "urinary specialist", "male health doctor"],
        "rheumatologist": ["rheumatologist", "arthritis specialist"],
        "allergist": ["allergist", "allergy doctor"],
        "general practitioner": ["general doctor", "family doctor", "primary care"],
    }

    user_message_lower = user_message.lower()

    for specialization, keywords in specialization_keywords.items():
        for keyword in keywords:
            if keyword in user_message_lower:
                logger.info(f"User explicitly requested a {specialization}")
                return specialization
    logger.debug("No explicit specialization mentioned by user")
    return None


def needs_doctor(user_message: str, response: str) -> bool:
    """
    Determine if the user or AI suggests the need to see a doctor.
    """
    doctor_indicators = [
        r"see a doctor",
        r"consult a doctor",
        r"visit a doctor",
        r"consult a specialist",
        r"need a doctor",
        r"medical attention",
        r"need to see",
        r"speak with a doctor",
        r"speak with a specialist",
        r"recommend a doctor",
        r"recommend a specialist",
        r"need professional help",
        r"might need to see a",
        r"should get in touch with a",
        r"consider seeing a",
    ]

    user_message_lower = user_message.lower()
    response_lower = response.lower()

    # Check for explicit mention in user's message or response
    for indicator in doctor_indicators:
        if re.search(indicator, user_message_lower) or re.search(
            indicator, response_lower
        ):
            logger.info(f"Found doctor indicator: {indicator}")
            return True
    logger.debug("No explicit doctor request found")
    return False


REMINDER_SYSTEM_PROMPT = """
You are a healthcare assistant bot focused solely on providing reminders for medication. Your role is to help users remember their medication schedules. 
Here’s how you should respond:
1. Generate a friendly and encouraging reminder message for the specified medication.
2. Include the medication name in a natural and engaging way.
3. Emphasize the importance of taking the medication as prescribed.
4. Maintain a positive and supportive tone in your responses.
"""


async def generate_reminder_message(medication_name: str) -> str:
    """
    Generate a reminder message using OpenAI's API.

    Args:
        medication_name (str): The name of the medication.

    Returns:
        str: A personalized reminder message.
    """
    user_message = f"Remind me to take my medication: {medication_name}."
    logger.info(f"Generating reminder message for medication: {medication_name}")

    try:
        conversation_history.append(
            {"role": "system", "content": REMINDER_SYSTEM_PROMPT}
        )
        conversation_history.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )

        answer = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": answer})

        logger.info(f"Generated reminder message: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Failed to generate reminder message: {e}")
        return f"Reminder: Please take your medication {medication_name}. Take care of yourself!"
