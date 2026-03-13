"""
简历解析模块
"""
from .resume_parser import ResumeParser, parse_resume
from .models import ResumeInfo, Education, WorkExperience, Project

__all__ = [
    "ResumeParser",
    "ResumeInfo",
    "Education",
    "WorkExperience",
    "Project",
    "parse_resume",
]
