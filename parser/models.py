"""
简历数据模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Education(BaseModel):
    """教育经历"""
    school: str = Field(default="", description="学校名称")
    major: str = Field(default="", description="专业")
    degree: str = Field(default="", description="学历: 本科/硕士/博士")
    start_date: Optional[str] = Field(default=None, description="开始时间")
    end_date: Optional[str] = Field(default=None, description="结束时间")


class WorkExperience(BaseModel):
    """工作经历"""
    company: str = Field(default="", description="公司名称")
    position: str = Field(default="", description="职位")
    start_date: Optional[str] = Field(default=None, description="开始时间")
    end_date: Optional[str] = Field(default=None, description="结束时间")
    description: str = Field(default="", description="工作描述")


class Project(BaseModel):
    """项目经历"""
    name: str = Field(default="", description="项目名称")
    role: str = Field(default="", description="角色")
    description: str = Field(default="", description="项目描述")


class ResumeInfo(BaseModel):
    """简历完整信息"""
    # 基本信息
    name: str = Field(default="", description="姓名")
    gender: str = Field(default="", description="性别")
    birthday: Optional[str] = Field(default=None, description="出生日期")
    phone: str = Field(default="", description="手机号")
    email: str = Field(default="", description="邮箱")
    location: str = Field(default="", description="现居地")
    
    # 求职意向
    intended_position: str = Field(default="", description="意向职位")
    expected_salary: Optional[str] = Field(default=None, description="期望薪资")
    
    # 教育经历
    education: List[Education] = Field(default_factory=list, description="教育经历")
    
    # 工作经历
    work_experience: List[WorkExperience] = Field(default_factory=list, description="工作经历")
    
    # 项目经历
    projects: List[Project] = Field(default_factory=list, description="项目经历")
    
    # 技能
    skills: List[str] = Field(default_factory=list, description="技能列表")
    
    # 自我评价
    self_evaluation: str = Field(default="", description="自我评价")
    
    def to_form_data(self) -> dict:
        """转换为表单数据格式"""
        return {
            "name": self.name,
            "gender": self.gender,
            "birthday": self.birthday or "",
            "phone": self.phone,
            "email": self.email,
            "location": self.location,
            "intended_position": self.intended_position,
            "expected_salary": self.expected_salary or "",
            "education": [edu.model_dump() for edu in self.education],
            "work_experience": [work.model_dump() for work in self.work_experience],
            "projects": [proj.model_dump() for proj in self.projects],
            "skills": ", ".join(self.skills),
            "self_evaluation": self.self_evaluation,
        }
