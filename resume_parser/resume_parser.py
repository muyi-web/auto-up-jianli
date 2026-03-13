"""
简历解析器 - 支持多种格式
"""
from pathlib import Path
from typing import Optional
from loguru import logger

from .models import ResumeInfo, Education, WorkExperience, Project
from .extractors import InfoExtractor


class ResumeParser:
    """简历解析器"""
    
    SUPPORTED_FORMATS = {".pdf", ".docx", ".doc", ".txt"}
    
    def __init__(self):
        self.extractor = InfoExtractor()
    
    def parse(self, file_path: str) -> ResumeInfo:
        """
        解析简历文件
        
        Args:
            file_path: 简历文件路径
            
        Returns:
            ResumeInfo: 结构化的简历信息
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"简历文件不存在: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {suffix}，支持的格式: {self.SUPPORTED_FORMATS}")
        
        logger.info(f"开始解析简历: {file_path}")
        
        # 根据格式选择解析方法
        if suffix == ".pdf":
            text = self._parse_pdf(path)
        elif suffix in [".docx", ".doc"]:
            text = self._parse_word(path)
        elif suffix == ".txt":
            text = self._parse_txt(path)
        else:
            raise ValueError(f"未知文件格式: {suffix}")
        
        # 提取结构化信息
        resume_info = self._extract_info(text)
        
        logger.info(f"简历解析完成: {resume_info.name}")
        
        return resume_info
    
    def _parse_pdf(self, path: Path) -> str:
        """解析 PDF 文件"""
        text = ""
        
        try:
            import pdfplumber
            
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
        except ImportError:
            logger.warning("pdfplumber 未安装，尝试使用 PyPDF2")
            import PyPDF2
            
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        
        return text.strip()
    
    def _parse_word(self, path: Path) -> str:
        """解析 Word 文件"""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("请安装 python-docx: pip install python-docx")
        
        doc = Document(path)
        
        # 提取所有段落
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        
        # 提取表格中的文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text.strip())
        
        return "\n".join(paragraphs)
    
    def _parse_txt(self, path: Path) -> str:
        """解析纯文本文件"""
        # 尝试多种编码
        encodings = ["utf-8", "gbk", "gb2312", "utf-16"]
        
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"无法解析文本文件，尝试了编码: {encodings}")
    
    def _extract_info(self, text: str) -> ResumeInfo:
        """从文本中提取结构化信息"""
        
        # 基本信息
        name = self.extractor.extract_name(text) or ""
        gender = self.extractor.extract_gender(text) or ""
        phone = self.extractor.extract_phone(text) or ""
        email = self.extractor.extract_email(text) or ""
        location = self.extractor.extract_location(text) or ""
        birthday = self.extractor.extract_birthday(text)
        
        # 复杂信息
        education_data = self.extractor.extract_education(text)
        work_data = self.extractor.extract_work_experience(text)
        skills = self.extractor.extract_skills(text)
        self_eval = self.extractor.extract_self_evaluation(text)
        
        # 构建 ResumeInfo
        resume_info = ResumeInfo(
            name=name,
            gender=gender,
            birthday=birthday,
            phone=phone,
            email=email,
            location=location,
            education=[Education(**edu) for edu in education_data],
            work_experience=[WorkExperience(**work) for work in work_data],
            skills=skills,
            self_evaluation=self_eval,
        )
        
        return resume_info


def parse_resume(file_path: str) -> ResumeInfo:
    """便捷函数：解析简历"""
    parser = ResumeParser()
    return parser.parse(file_path)
