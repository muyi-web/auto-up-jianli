"""
智能表单填写器 - 通用的表单自动填写逻辑
"""
import re
from typing import Dict, List, Optional, Tuple
from loguru import logger
from playwright.sync_api import Page, Locator

from parser.models import ResumeInfo


class SmartFormFiller:
    """
    智能表单填写器
    
    通过分析表单元素的 label、placeholder、name 等属性，
    智能匹配简历信息进行自动填写
    """
    
    # 字段关键词映射 - 用于识别表单字段含义
    FIELD_KEYWORDS = {
        # 基本信息
        "name": ["姓名", "名字", "真实姓名", "name", "用户名", "称呼"],
        "gender": ["性别", "gender", "男", "女"],
        "phone": ["手机", "电话", "联系方式", "mobile", "phone", "tel", "联系电话"],
        "email": ["邮箱", "email", "mail", "电子邮箱", "邮件"],
        "birthday": ["出生", "生日", "birthday", "出生日期", "出生年月"],
        "location": ["地址", "居住", "所在地", "现居", "城市", "city", "location", "住址"],
        "id_card": ["身份证", "证件号", "idcard", "身份证号"],
        
        # 教育相关
        "school": ["学校", "院校", "school", "university", "毕业院校"],
        "major": ["专业", "major", "所学专业"],
        "degree": ["学历", "学位", "degree", "education", "最高学历"],
        "education_start": ["入学", "入学时间", "education_start"],
        "education_end": ["毕业", "毕业时间", "education_end"],
        
        # 工作相关
        "company": ["公司", "企业", "company", "工作单位", "所在公司"],
        "position": ["职位", "岗位", "position", "job", "职务", "职称"],
        "work_start": ["入职", "入职时间", "work_start"],
        "work_end": ["离职", "离职时间", "work_end"],
        "work_desc": ["工作内容", "工作描述", "职责", "description", "工作职责"],
        
        # 求职意向
        "intended_position": ["意向职位", "期望职位", "应聘职位", "求职意向"],
        "expected_salary": ["期望薪资", "薪资要求", "salary", "期望工资"],
        
        # 其他
        "skills": ["技能", "特长", "skill", "专业技能", "技术栈"],
        "self_intro": ["自我介绍", "自我评价", "个人简介", "introduction", "自我描述"],
        "project": ["项目", "project", "项目经历", "项目经验"],
    }
    
    # 性别选项映射
    GENDER_OPTIONS = {
        "male": ["男", "男性", "男同学", "先生", "male", "m", "1"],
        "female": ["女", "女性", "女同学", "女士", "female", "f", "2"],
    }
    
    # 学历选项映射
    DEGREE_OPTIONS = {
        "doctor": ["博士", "doctor", "phd", "博士研究生"],
        "master": ["硕士", "master", "硕士研究生", "研究生"],
        "bachelor": ["本科", "bachelor", "大学本科", "学士"],
        "college": ["大专", "专科", "college", "高职"],
        "high_school": ["高中", "中专", "高中及以下"],
    }
    
    def __init__(self, page: Page, resume: ResumeInfo):
        self.page = page
        self.resume = resume
        
        # 准备简历数据映射
        self.resume_data = self._build_resume_data()
    
    def _build_resume_data(self) -> Dict[str, any]:
        """构建简历数据映射"""
        return {
            "name": self.resume.name,
            "gender": self.resume.gender,
            "phone": self.resume.phone,
            "email": self.resume.email,
            "birthday": self.resume.birthday,
            "location": self.resume.location,
            "intended_position": self.resume.intended_position,
            "expected_salary": self.resume.expected_salary,
            "skills": ", ".join(self.resume.skills),
            "self_intro": self.resume.self_evaluation,
        }
    
    def fill_all_forms(self) -> int:
        """
        自动识别并填写页面上的所有表单
        
        Returns:
            成功填写的字段数量
        """
        filled_count = 0
        
        # 1. 处理文本输入框
        filled_count += self._fill_input_fields()
        
        # 2. 处理下拉选择框
        filled_count += self._fill_select_fields()
        
        # 3. 处理单选框（性别等）
        filled_count += self._fill_radio_fields()
        
        # 4. 处理多行文本框
        filled_count += self._fill_textarea_fields()
        
        logger.info(f"表单填写完成，共填写 {filled_count} 个字段")
        return filled_count
    
    def _fill_input_fields(self) -> int:
        """填写所有文本输入框"""
        count = 0
        inputs = self.page.locator("input:not([type='hidden']):not([type='radio']):not([type='checkbox']):not([type='submit']):not([type='button'])")
        
        total = inputs.count()
        for i in range(total):
            try:
                input_elem = inputs.nth(i)
                if not input_elem.is_visible():
                    continue
                
                # 获取字段信息
                field_info = self._analyze_input_field(input_elem, i)
                
                if field_info and field_info["type"] in self.resume_data:
                    value = self.resume_data[field_info["type"]]
                    if value:
                        input_elem.fill(str(value))
                        logger.debug(f"填写 {field_info['type']}: {value}")
                        count += 1
            except Exception as e:
                logger.debug(f"填写输入框失败: {e}")
                continue
        
        return count
    
    def _fill_select_fields(self) -> int:
        """填写所有下拉选择框"""
        count = 0
        selects = self.page.locator("select")
        
        total = selects.count()
        for i in range(total):
            try:
                select_elem = selects.nth(i)
                if not select_elem.is_visible():
                    continue
                
                # 分析下拉框类型
                field_type = self._analyze_select_field(select_elem, i)
                
                if field_type:
                    value = self._get_select_value(select_elem, field_type)
                    if value:
                        select_elem.select_option(value)
                        logger.debug(f"选择 {field_type}: {value}")
                        count += 1
            except Exception as e:
                logger.debug(f"选择下拉框失败: {e}")
                continue
        
        return count
    
    def _fill_radio_fields(self) -> int:
        """填写单选框（主要用于性别选择）"""
        count = 0
        
        # 处理性别单选
        gender_radios = self.page.locator("input[type='radio']")
        total = gender_radios.count()
        
        gender_filled = False
        
        for i in range(total):
            try:
                radio = gender_radios.nth(i)
                if not radio.is_visible():
                    continue
                
                # 获取关联的 label
                label = self._get_label_for_element(radio)
                
                # 判断是否为性别选项
                if label and self._contains_keywords(label, self.FIELD_KEYWORDS["gender"]):
                    # 判断是男还是女
                    label_lower = label.lower()
                    if self.resume.gender == "男" and any(k in label_lower for k in self.GENDER_OPTIONS["male"]):
                        radio.click()
                        count += 1
                        gender_filled = True
                    elif self.resume.gender == "女" and any(k in label_lower for k in self.GENDER_OPTIONS["female"]):
                        radio.click()
                        count += 1
                        gender_filled = True
                    
                    if gender_filled:
                        break
            except Exception as e:
                logger.debug(f"选择单选框失败: {e}")
                continue
        
        return count
    
    def _fill_textarea_fields(self) -> int:
        """填写多行文本框"""
        count = 0
        textareas = self.page.locator("textarea")
        
        total = textareas.count()
        for i in range(total):
            try:
                textarea = textareas.nth(i)
                if not textarea.is_visible():
                    continue
                
                # 分析文本框类型
                field_info = self._analyze_textarea_field(textarea, i)
                
                if field_info and field_info["type"] in self.resume_data:
                    value = self.resume_data[field_info["type"]]
                    if value:
                        textarea.fill(str(value))
                        logger.debug(f"填写 {field_info['type']}")
                        count += 1
            except Exception as e:
                logger.debug(f"填写文本框失败: {e}")
                continue
        
        return count
    
    def _analyze_input_field(self, elem: Locator, index: int) -> Optional[Dict]:
        """分析输入框字段类型"""
        # 收集所有可能标识该字段的文本
        identifiers = []
        
        # 1. name 属性
        name = elem.get_attribute("name") or ""
        if name:
            identifiers.append(name)
        
        # 2. placeholder 属性
        placeholder = elem.get_attribute("placeholder") or ""
        if placeholder:
            identifiers.append(placeholder)
        
        # 3. id 属性
        elem_id = elem.get_attribute("id") or ""
        if elem_id:
            identifiers.append(elem_id)
        
        # 4. aria-label 属性
        aria_label = elem.get_attribute("aria-label") or ""
        if aria_label:
            identifiers.append(aria_label)
        
        # 5. 关联的 label
        label = self._get_label_for_element(elem)
        if label:
            identifiers.append(label)
        
        # 6. 附近的文本（父元素或前一个兄弟元素）
        nearby_text = self._get_nearby_text(elem)
        if nearby_text:
            identifiers.append(nearby_text)
        
        # 合并所有标识符
        all_text = " ".join(identifiers).lower()
        
        # 匹配字段类型
        for field_type, keywords in self.FIELD_KEYWORDS.items():
            if self._contains_keywords(all_text, keywords):
                return {"type": field_type, "identifiers": identifiers}
        
        return None
    
    def _analyze_select_field(self, elem: Locator, index: int) -> Optional[str]:
        """分析下拉框字段类型"""
        identifiers = []
        
        name = elem.get_attribute("name") or ""
        if name:
            identifiers.append(name)
        
        elem_id = elem.get_attribute("id") or ""
        if elem_id:
            identifiers.append(elem_id)
        
        label = self._get_label_for_element(elem)
        if label:
            identifiers.append(label)
        
        # 获取选项文本
        try:
            options = elem.locator("option")
            option_texts = []
            for i in range(options.count()):
                text = options.nth(i).text_content() or ""
                option_texts.append(text)
            identifiers.extend(option_texts)
        except:
            pass
        
        all_text = " ".join(identifiers).lower()
        
        # 匹配字段类型
        for field_type, keywords in self.FIELD_KEYWORDS.items():
            if self._contains_keywords(all_text, keywords):
                return field_type
        
        return None
    
    def _analyze_textarea_field(self, elem: Locator, index: int) -> Optional[Dict]:
        """分析文本域字段类型"""
        identifiers = []
        
        name = elem.get_attribute("name") or ""
        if name:
            identifiers.append(name)
        
        placeholder = elem.get_attribute("placeholder") or ""
        if placeholder:
            identifiers.append(placeholder)
        
        elem_id = elem.get_attribute("id") or ""
        if elem_id:
            identifiers.append(elem_id)
        
        label = self._get_label_for_element(elem)
        if label:
            identifiers.append(label)
        
        all_text = " ".join(identifiers).lower()
        
        # 匹配字段类型
        for field_type, keywords in self.FIELD_KEYWORDS.items():
            if self._contains_keywords(all_text, keywords):
                return {"type": field_type}
        
        return None
    
    def _get_label_for_element(self, elem: Locator) -> Optional[str]:
        """获取元素关联的 label 文本"""
        try:
            # 方法1: 通过 for 属性关联
            elem_id = elem.get_attribute("id")
            if elem_id:
                label = self.page.locator(f"label[for='{elem_id}']")
                if label.count() > 0:
                    return label.first.text_content()
            
            # 方法2: label 包裹 input
            parent = elem.locator("xpath=ancestor::label")
            if parent.count() > 0:
                return parent.first.text_content()
            
            # 方法3: 前一个兄弟 label 元素
            prev_label = elem.locator("xpath=preceding-sibling::label")
            if prev_label.count() > 0:
                return prev_label.first.text_content()
            
            # 方法4: 查找父元素中的 label
            parent_label = elem.locator("xpath=..//label")
            if parent_label.count() > 0:
                text = parent_label.first.text_content()
                if text:
                    return text
            
        except Exception as e:
            logger.debug(f"获取 label 失败: {e}")
        
        return None
    
    def _get_nearby_text(self, elem: Locator) -> Optional[str]:
        """获取元素附近的文本（前一个兄弟元素或父元素的文本）"""
        try:
            # 尝试获取前一个兄弟元素
            prev = elem.locator("xpath=preceding-sibling::*[1]")
            if prev.count() > 0:
                text = prev.first.text_content()
                if text and len(text) < 50:  # 限制长度避免获取太多无关内容
                    return text
            
            # 尝试获取父元素的文本
            parent = elem.locator("xpath=..")
            if parent.count() > 0:
                text = parent.first.text_content()
                if text and len(text) < 100:
                    return text
            
        except Exception as e:
            logger.debug(f"获取附近文本失败: {e}")
        
        return None
    
    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本是否包含关键词"""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    
    def _get_select_value(self, select_elem: Locator, field_type: str) -> Optional[str]:
        """根据字段类型获取下拉框应该选择的值"""
        try:
            options = select_elem.locator("option")
            option_list = []
            
            for i in range(options.count()):
                option = options.nth(i)
                value = option.get_attribute("value") or ""
                text = option.text_content() or ""
                option_list.append((value, text))
            
            # 根据字段类型匹配选项
            if field_type == "gender":
                return self._match_gender_option(option_list)
            elif field_type == "degree":
                return self._match_degree_option(option_list)
            elif field_type in self.resume_data:
                # 尝试直接匹配
                target_value = str(self.resume_data[field_type])
                for value, text in option_list:
                    if target_value in text or target_value in value:
                        return value
        
        except Exception as e:
            logger.debug(f"获取选择值失败: {e}")
        
        return None
    
    def _match_gender_option(self, options: List[Tuple[str, str]]) -> Optional[str]:
        """匹配性别选项"""
        target_keywords = self.GENDER_OPTIONS["male"] if self.resume.gender == "男" else self.GENDER_OPTIONS["female"]
        
        for value, text in options:
            if any(kw in text.lower() for kw in target_keywords):
                return value
        
        return None
    
    def _match_degree_option(self, options: List[Tuple[str, str]]) -> Optional[str]:
        """匹配学历选项"""
        for degree_type, keywords in self.DEGREE_OPTIONS.items():
            if any(kw in self.resume.education[0].degree for kw in keywords) if self.resume.education else False:
                for value, text in options:
                    if any(kw in text for kw in keywords):
                        return value
        
        return None
