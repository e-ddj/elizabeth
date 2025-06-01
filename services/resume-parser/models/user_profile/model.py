import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Union

from core.user_profile.types import (
    UserData,
    UserEducation,
    UserProfile,
    UserExperience,
)
from utils.data_utils import normalize_input
from utils.openai.client import create_client
from utils.openai.prompting import send_prompt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ───────────────────────────── prompt helpers ─────────────────────────────
# (Every prompt and output format is verbatim from the original file)
def edu_extract(resume_text, openai_client) -> Optional[List[UserEducation]]:
    prompt = f"""
                Extract all the all diplomas listed in the following CV. 
                Do not invent any data. Do not impute. Be as accurate as possible. If not accurate please omit.
                If you can't retrieve the location (city/country) explicitely, try to infer it from the educational establishment.
                Provide the diploma title, the start year if possible, the graduation year and a brief description of the diploma in the format:
                "Job Title": ["Diploma", "Educational Establishment", "City", "Country", "Start Year "YYYY"", "Graduation Year "YYYY""].
                
                CV:
                {resume_text}
                
                Output format:
                {{
                "Diploma 1": ["Diploma 1", "Educational Establishment 1", "Diploma 1 obtained in Country", "Diploma 1 obtained in City", "Diploma 1 Start year YYYY", "Diploma 1 Graduation year YYYY"],
                "Diploma 2": ["Diploma 2",  "Educational Establishment 2", "Diploma 2 obtained in Country", "Diploma 2 obtained in City", "Diploma 2 Start year YYYY", "Diploma 2 Graduation year YYYY"],
                ...
                }}
                
                Additional instructions:
                - It is possible that there is no start date but only a graduation date/year or an issued date/year, in which case you should set the start date/year to null.
                """
    return send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that extracts educational information from CVs.",
    )


def experiences_extract(resume_text, openai_client) -> Optional[List[UserExperience]]:
    prompt = f"""
                Extract all the jobs including previous ones listed in the following CV. 
                Do not invent any data. Do not impute. Be as accurate as possible. If not accurate please omit.
                If you can't retrieve the location (city/country) explicitely, try to infer it from the job experience.
                Provide the job title and a brief description of the role in the format:
                "Job Title": ["Medical Facility without location", "City", "Country", "Job Start "MM/YYYY"", "Job End "MM/YYYY""].
                
                CV:
                {resume_text}
                
                Output format:
                {{
                "Job Title 1": ["Job 1 Medical Facility without location", "Job 1 City", "Job 1 Country", "Job 1 Start MM/YYYY", "Job 1 End MM/YYYY"],
                "Job Title 2": ["Job 2 Medical Facility without location",  "Job 2 City", "Job 2 Country", "Job 2 Start MM/YYYY", "Job 2 End "MM/YYYY"],
                ...
                }}
                """
    return send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that extracts jobs information from CVs.",
    )


def about_extract(resume_text, openai_client):
    prompt = f"""
                Extract all information about the owner of the CV in the following CV. 
                Do not invent any data. Do not impute. Be as accurate as possible. If not accurate please omit.
                Provide the details and a brief description in the format:
                If the address country is not explicitely written, try to deduce it from the current job position if mentionned.
                ["Title", "First Name", "Last Name", "Position", "Address Street", "Address City", "Address Country in alpha2 code", "Phone Number", "Citizenships in alpha2 code", "Can you describe the whole CV in two or the sentences here and frame it in an implied first-person style, which is typical for professional summaries in CVs and resumes."].
                
                CV:
                {resume_text}
                
                Output format:
                "["Title", "First Name", "Last Name", "Position", "Address Street", "Address City", "Address Country in alpha2 code", "Phone Number", "Citizenships in alpha2 code", "Can you describe the whole CV in two or the sentences and frame it in an implied first-person style, which is typical for professional summaries in CVs and resumes."]
                """
    extract = send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that extracts information about the owner from CVs",
    )
    return extract if isinstance(extract, list) else []


def languages_extract(resume_text, openai_client):
    prompt = f"""
                Extract all languages spoken by the owner of the following CV. Do not invent any data. Do not impute. Be as accurate as possible. If not accurate please omit.
                Provide the languages in the format:
                "Language 1": ["Language"].
                
                CV:
                {resume_text}
                
                Output format:
                {{
                "Language 1": ["Language 1"],
                "Language 2": ["Language 2"],
                    ...
                }}
                """
    return send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that extracts spoken languages from CVs.",
    )


def certifications_extract(resume_text, openai_client):
    prompt = f"""
                Extract all the all medical certificats and other professional certificats listed in the following CV. Do not report anything about education. Do not invent any data. Do not impute. Be as accurate as possible. If not accurate please omit.
                Provide the certificat title and a brief description of the certificate in the format:
                "Certificat": ["Certificat", "Certificate Issuing Authority", "City", "Country", "Issue Date "YYYY""].
                
                CV:
                {resume_text}
                
                Output format:
                {{
                "Certificat 1": ["Certificat 1", "Certificate Issuing Authority 1", "Certificate 1 obtained in Country", "Certificate 1 obtained in City", "Certificate 1 Issue Date MM/YYYY"],
                "Certificat 2": ["Certificat 2",  "Certificate Issuing Authority 2", "Certificate 2 obtained in Country", "Certificate 2 obtained in City", "Certificate 2 Issue Date MM/YYYY"],
                    ...
                }}
                """
    return send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that extracts information about certificates from CVs",
    )


def publications(resume_text, openai_client):
    prompt = f"""
                Extract all the all medical research publications from the following CV. Do not invent any data. Do not impute. Be as accurate as possible. If not accurate please omit.
                Provide the research publication title and a brief description in the format:
                "Publication": ["Publication title", "Scientific Journal", "Publication Date "YYYY""].
                
                CV:
                {resume_text}
                
                Output format:
                {{
                "Publication 1": ["Publication title 1", "Scientific Journal 1", "Publication 1 Date YYYY"],
                "Publication 2": ["Publication title 2",  "Scientific Journal 2", "Publication 2 Date YYYY"],
                    ...
                }}
                """
    return send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that extracts information about publications from CVs",
    )


def rosette_name_extract(text: str, openai_client, medical_specialties: List[str]):
    prompt = f"""
                Instructions:
                I have a python list with medical specialties that I will give you first. 
                I will then give you the description of a job. 
                I want you to match it with the list and give me the closest match. 
                If the offer is looking for a resident pyshician please indicate what the specialization is. 
                If there is no close match please use None as output.
                It may be that the job description is not in english but you will try to match nonetheless with the job list we are providing.
            
                Medical specialties list:
                {medical_specialties}
                
                Job information from the job offer:              
                {text}
                
                Output format:
                Please only give one exact value from the python list in the beginning, nothing else and do not modify the value. 
                if nothing matches please use None as output.:
                """
    return send_prompt(
        client=openai_client,
        prompt=prompt,
        system_message="You are a helpful assistant that matches information about jobs from job offers.",
    )


def find_speciality(identified_spe_name, rosetta_specialties, openai_client):
    try:
        matched = next(
            (spe for spe in rosetta_specialties if spe["name"] == identified_spe_name),
            None,
        )
        return matched["id_rosetta"] if matched else None
    except Exception:
        return None


def parse_date(date_str: str) -> Optional[datetime.date]:
    try:
        date_str = date_str.replace("Job Start ", "").replace("Job End ", "")
        if date_str.lower() == "present":
            return None
        return datetime.datetime.strptime(date_str, "%m/%Y").date()
    except Exception:
        return None


# ────────────────────────── safety utility ──────────────────────────
def _ensure_dict(raw: Union[str, Dict[str, Any]], field: str) -> Dict[str, Any]:
    """
    Always return a dict; if raw is a string, try JSON‑decode, else log & {}.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, dict):
                return decoded
            logger.warning("Field '%s' JSON‑decoded to %s, expected dict.", field, type(decoded))
        except json.JSONDecodeError:
            logger.warning("Field '%s' is string but not valid JSON.", field)
        return {}
    logger.warning("Field '%s' has unexpected type %s; coerced to dict.", field, type(raw))
    return {}


# ───────────────────────────── main function ─────────────────────────────
def run_model(
    resume_text: Optional[str], rosetta_medical_specialties, local_medical_specialties
) -> UserData:
    if not resume_text:
        raise Exception("CV text cannot be empty")

    openai_client = create_client()
    rosetta_specialties = rosetta_medical_specialties.data
    rosetta_names = [spe["name"] for spe in rosetta_specialties]

    # ---------- EXPERIENCES ----------
    exp_raw = experiences_extract(resume_text, openai_client)
    experience_dict = _ensure_dict(exp_raw, "experience")

    concat_titles = ", ".join(experience_dict) if experience_dict else None
    identified_spe_name = (
        rosette_name_extract(concat_titles, openai_client, rosetta_names)
        if concat_titles
        else None
    )

    user_experiences: List[UserExperience] = []
    for pos, details in experience_dict.items():
        if isinstance(details, list) and len(details) == 5:
            user_experiences.append(
                UserExperience(
                    position=pos,
                    specialty=identified_spe_name,
                    rosetta_id=find_speciality(identified_spe_name, rosetta_specialties, openai_client),
                    organization=details[0],
                    city=details[1],
                    country=details[2],
                    start_date=parse_date(details[3]),
                    end_date=parse_date(details[4]),
                )
            )

    # ---------- EDUCATION ----------
    edu_raw = edu_extract(resume_text, openai_client)
    edu_dict = _ensure_dict(edu_raw, "education")

    user_diplomas: List[UserEducation] = []
    for _, details in edu_dict.items():
        if isinstance(details, list) and len(details) == 6:
            user_diplomas.append(
                UserEducation(
                    degree=details[0],
                    organization=details[1],
                    country=details[2],
                    city=details[3],
                    start_year=details[4],
                    end_year=details[5],
                )
            )

    # ---------- PERSONAL INFO ----------
    about_list = about_extract(resume_text, openai_client) or []
    about_list.extend([None] * (10 - len(about_list)))
    about = UserProfile(
        title=about_list[0] or "",
        first_name=about_list[1] or "",
        last_name=about_list[2] or "",
        position=about_list[3] or "",
        street=about_list[4] or "",
        city=about_list[5] or "",
        country=about_list[6] or "",
        phone=about_list[7] or "",
        citizenships=normalize_input(about_list[8] or None),
        about_me=about_list[9] or "",
        specialties=None,
        extracted_resume=resume_text,
    )

    # ---------- ASSEMBLE ----------
    return UserData(
        user_id=None,
        profile=about,
        experiences=user_experiences,
        educations=user_diplomas,
        languages=None,
        certifications=None,
        publications=None,
        criteria=None,
    )