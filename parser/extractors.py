"""
信息提取器 - 从简历文本中提取结构化信息
"""
import re
from typing import Optional, List
from loguru import logger

import jieba


class InfoExtractor:
    """信息提取器"""
    
    # 性别关键词
    GENDER_MALE = ["男", "男性", "先生", "男生"]
    GENDER_FEMALE = ["女", "女性", "女士", "女生"]
    
    # 学历关键词
    DEGREE_KEYWORDS = ["博士", "硕士", "研究生", "本科", "大专", "专科", "学士", "MBA"]
    
    def __init__(self):
        # 加载自定义词典
        self._load_custom_dict()
    
    def _load_custom_dict(self):
        """加载自定义词典，提高分词准确度"""
        # 添加常见学校名
        common_schools = [
            "清华大学", "北京大学", "浙江大学", "复旦大学", "上海交通大学",
            "南京大学", "武汉大学", "中山大学", "四川大学", "华中科技大学",
            "哈尔滨工业大学", "西安交通大学", "中国科学技术大学", "北京航空航天大学"
        ]
        for school in common_schools:
            jieba.add_word(school, freq=1000)
    
    def extract_name(self, text: str) -> Optional[str]:
        """提取姓名"""
        # 尝试多种模式
        patterns = [
            r"姓\s*名[：:]\s*([^\s\n]+)",
            r"姓\s*名\s*([^\s\n]+)",
            r"^[^\s]{2,4}$",  # 单独一行的姓名
        ]
        
        lines = text.strip().split("\n")
        
        # 第一行通常是姓名
        if lines:
            first_line = lines[0].strip()
            if 2 <= len(first_line) <= 4 and not any(k in first_line for k in ["电话", "邮箱", "教育", "经历"]):
                return first_line
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_gender(self, text: str) -> Optional[str]:
        """提取性别"""
        text_lower = text.lower()
        
        for keyword in self.GENDER_MALE:
            if keyword in text_lower:
                return "男"
        
        for keyword in self.GENDER_FEMALE:
            if keyword in text_lower:
                return "女"
        
        # 尝试匹配性别字段
        match = re.search(r"性\s*别[：:]\s*([男女])", text)
        if match:
            return match.group(1)
        
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """提取手机号"""
        # 匹配中国大陆手机号
        patterns = [
            r"(?:电话|手机|联系方式|Tel|Phone)[：:]*\s*(\d{11})",
            r"(?:电话|手机|联系方式|Tel|Phone)[：:]*\s*([\d-]+)",
            r"(1[3-9]\d{9})",  # 直接匹配手机号
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(1).replace("-", "")
                if len(phone) == 11:
                    return phone
        
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """提取邮箱"""
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_location(self, text: str) -> Optional[str]:
        """提取现居地"""
        patterns = [
            r"(?:现居|居住地|所在地|地址|住址)[：:]\s*([^\n]+)",
            r"(?:现居|居住地|所在地|地址|住址)\s*[:：]?\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_birthday(self, text: str) -> Optional[str]:
        """提取出生日期"""
        patterns = [
            r"(?:出生日期|出生年月|生日|出生)[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)",
            r"(?:出生日期|出生年月|生日|出生)[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            r"(?:年龄|岁数)[：:]\s*(\d+)岁?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_education(self, text: str) -> List[dict]:
        """提取教育经历"""
        education_list = []
        
        # 查找教育经历部分
        edu_section = self._extract_section(text, ["教育经历", "教育背景", "求学经历", "学历"])
        
        if not edu_section:
            return education_list
        
        # 按行分割
        lines = edu_section.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            edu_info = {
                "school": "",
                "major": "",
                "degree": "",
                "start_date": None,
                "end_date": None,
            }
            
            # 提取学历
            for degree in self.DEGREE_KEYWORDS:
                if degree in line:
                    edu_info["degree"] = degree
                    break
            
            # 提取时间
            time_match = re.search(r"(\d{4})\s*[-/~至]\s*(\d{4}|至今|现在)", line)
            if time_match:
                edu_info["start_date"] = time_match.group(1)
                edu_info["end_date"] = time_match.group(2) if time_match.group(2) not in ["至今", "现在"] else None
            
            # 尝试提取学校和专业
            # 简单策略: 假设学校在前，专业在后
            parts = re.split(r"[\s|,，、]+", line)
            for part in parts:
                part = part.strip()
                if not part or any(k in part for k in ["本科", "硕士", "博士", "大专", "专科"]):
                    continue
                if "大学" in part or "学院" in part:
                    edu_info["school"] = part
                elif not edu_info["school"]:
                    edu_info["school"] = part
                elif not edu_info["major"]:
                    edu_info["major"] = part
            
            if edu_info["school"] or edu_info["major"]:
                education_list.append(edu_info)
        
        return education_list
    
    def extract_work_experience(self, text: str) -> List[dict]:
        """提取工作经历"""
        work_list = []
        
        # 查找工作经历部分
        work_section = self._extract_section(text, ["工作经历", "工作背景", "工作经验", "职业经历"])
        
        if not work_section:
            return work_list
        
        lines = work_section.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            work_info = {
                "company": "",
                "position": "",
                "start_date": None,
                "end_date": None,
                "description": "",
            }
            
            # 提取时间
            time_match = re.search(r"(\d{4}[./-]\d{1,2})\s*[-/~至]\s*(\d{4}[./-]\d{1,2}|至今|现在)", line)
            if time_match:
                work_info["start_date"] = time_match.group(1)
                work_info["end_date"] = time_match.group(2) if time_match.group(2) not in ["至今", "现在"] else None
            
            # 简单提取公司和职位
            parts = re.split(r"[\s|,，、]+", line)
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                if not work_info["company"]:
                    work_info["company"] = part
                elif not work_info["position"]:
                    work_info["position"] = part
                else:
                    work_info["description"] += part + " "
            
            if work_info["company"]:
                work_list.append(work_info)
        
        return work_list
    
    def extract_skills(self, text: str) -> List[str]:
        """提取技能"""
        skills = []
        
        # 查找技能部分
        skill_section = self._extract_section(text, ["专业技能", "技能特长", "技能", "技术栈", "掌握技能"])
        
        if skill_section:
            # 按常见分隔符分割
            skill_text = re.sub(r"[\n、,，；;]", " ", skill_section)
            skills = [s.strip() for s in skill_text.split() if s.strip() and len(s.strip()) > 1]
        
        return skills[:20]  # 限制数量
    
    def extract_self_evaluation(self, text: str) -> str:
        """提取自我评价"""
        return self._extract_section(text, ["自我评价", "个人总结", "个人简介", "自我介绍", "简介"]) or ""
    
    def _extract_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """提取特定部分的内容"""
        for keyword in keywords:
            # 尝试找到该部分的开始
            pattern = rf"{keyword}[\s:：]*\n?(.*?)(?=\n\s*\n|\n[A-Z\u4e00-\u9fa5]{{2,8}}\s*[:：]|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
