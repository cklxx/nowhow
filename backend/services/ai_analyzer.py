import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
import re
import os
from datetime import datetime

from models.source_config import (
    AIAnalysisRequest, AIAnalysisResult, ContentSelector, 
    ContentType, AuthType, CrawlConfig
)

class AIWebAnalyzer:
    """AI网页结构分析器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("ARK API key is required")
        
        self.api_base = "https://ark.cn-beijing.volces.com/api/v3"
        self.model = "ep-20250617155129-hfzl9"
    
    async def analyze_webpage(self, request: AIAnalysisRequest) -> AIAnalysisResult:
        """分析网页结构并生成抓取配置"""
        try:
            # 1. 获取网页内容
            html_content = await self._fetch_webpage(str(request.url))
            
            # 2. 解析HTML结构
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 3. 提取页面基本信息
            page_info = self._extract_page_info(soup, str(request.url))
            
            # 4. 分析页面结构
            structure_analysis = self._analyze_page_structure(soup)
            
            # 5. 使用AI生成选择器
            ai_selectors = await self._generate_selectors_with_ai(
                html_content, str(request.url), request.content_type, structure_analysis
            )
            
            # 6. 验证和优化选择器
            validated_selectors = self._validate_selectors(soup, ai_selectors)
            
            # 7. 生成分析结果
            result = AIAnalysisResult(
                url=str(request.url),
                confidence=validated_selectors.get("confidence", 0.8),
                suggested_selectors=ContentSelector(**validated_selectors.get("selectors", {})),
                page_structure=structure_analysis,
                content_patterns=self._identify_content_patterns(soup),
                recommendations=self._generate_recommendations(page_info, structure_analysis),
                potential_issues=self._identify_potential_issues(soup, str(request.url)),
                requires_auth=self._check_auth_requirement(soup, html_content),
                requires_js=self._check_js_requirement(soup),
                estimated_quality=self._estimate_content_quality(soup, structure_analysis)
            )
            
            return result
            
        except Exception as e:
            # 返回默认分析结果
            return AIAnalysisResult(
                url=str(request.url),
                confidence=0.3,
                suggested_selectors=ContentSelector(),
                page_structure={"error": str(e)},
                content_patterns=[],
                recommendations=[f"分析失败: {str(e)}"],
                potential_issues=["无法完成自动分析"],
                requires_auth=False,
                requires_js=False,
                estimated_quality=0.5
            )
    
    async def _fetch_webpage(self, url: str) -> str:
        """获取网页内容"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise Exception(f"HTTP {response.status}: Failed to fetch {url}")
    
    def _extract_page_info(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """提取页面基本信息"""
        info = {
            "title": "",
            "description": "",
            "keywords": "",
            "language": "",
            "charset": "",
            "viewport": "",
            "canonical": "",
            "has_rss": False,
            "social_meta": {}
        }
        
        # 标题
        title_tag = soup.find('title')
        if title_tag:
            info["title"] = title_tag.get_text().strip()
        
        # Meta信息
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                info["description"] = content
            elif name == 'keywords':
                info["keywords"] = content
            elif name == 'language':
                info["language"] = content
            elif name == 'viewport':
                info["viewport"] = content
            elif property_attr.startswith('og:'):
                info["social_meta"][property_attr] = content
            elif name.startswith('twitter:'):
                info["social_meta"][name] = content
        
        # 语言
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            info["language"] = html_tag.get('lang')
        
        # 字符集
        charset_meta = soup.find('meta', charset=True)
        if charset_meta:
            info["charset"] = charset_meta.get('charset')
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            info["canonical"] = canonical.get('href', '')
        
        # RSS链接
        rss_links = soup.find_all('link', type='application/rss+xml')
        info["has_rss"] = len(rss_links) > 0
        
        return info
    
    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """分析页面结构"""
        structure = {
            "total_elements": len(soup.find_all()),
            "headings": {},
            "content_containers": [],
            "navigation_elements": [],
            "sidebar_elements": [],
            "footer_elements": [],
            "form_elements": [],
            "media_elements": {},
            "semantic_elements": [],
            "class_patterns": {},
            "id_patterns": {}
        }
        
        # 分析标题层次
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            structure["headings"][f"h{level}"] = len(headings)
        
        # 分析语义元素
        semantic_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        for tag in semantic_tags:
            elements = soup.find_all(tag)
            if elements:
                structure["semantic_elements"].append({
                    "tag": tag,
                    "count": len(elements),
                    "selectors": [self._generate_selector(elem) for elem in elements[:3]]
                })
        
        # 分析可能的内容容器
        content_candidates = soup.find_all(['div', 'section', 'article'], class_=True)
        for elem in content_candidates:
            classes = ' '.join(elem.get('class', []))
            if any(keyword in classes.lower() for keyword in ['content', 'main', 'body', 'article', 'post']):
                structure["content_containers"].append({
                    "selector": self._generate_selector(elem),
                    "classes": classes,
                    "text_length": len(elem.get_text().strip())
                })
        
        # 分析导航元素
        nav_elements = soup.find_all(['nav', 'div'], class_=lambda x: x and any(
            nav_word in ' '.join(x).lower() for nav_word in ['nav', 'menu', 'header']
        ))
        for elem in nav_elements[:5]:
            structure["navigation_elements"].append(self._generate_selector(elem))
        
        # 分析媒体元素
        structure["media_elements"] = {
            "images": len(soup.find_all('img')),
            "videos": len(soup.find_all('video')),
            "audio": len(soup.find_all('audio')),
            "iframes": len(soup.find_all('iframe'))
        }
        
        # 分析表单元素
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            structure["form_elements"].append({
                "action": form.get('action', ''),
                "method": form.get('method', 'GET'),
                "inputs": len(inputs),
                "has_submit": bool(form.find(['input', 'button'], type='submit'))
            })
        
        # 分析class模式
        all_classes = []
        for elem in soup.find_all(class_=True):
            all_classes.extend(elem.get('class', []))
        
        class_freq = {}
        for cls in all_classes:
            class_freq[cls] = class_freq.get(cls, 0) + 1
        
        # 保存最常见的class
        sorted_classes = sorted(class_freq.items(), key=lambda x: x[1], reverse=True)
        structure["class_patterns"] = dict(sorted_classes[:20])
        
        return structure
    
    async def _generate_selectors_with_ai(self, html_content: str, url: str, 
                                        content_type: ContentType, 
                                        structure: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI生成选择器"""
        
        # 截取HTML样本（前8000字符）
        html_sample = html_content[:8000] if len(html_content) > 8000 else html_content
        
        # 构建提示
        prompt = self._build_analysis_prompt(url, html_sample, content_type, structure)
        
        try:
            # 调用AI API
            response = await self._call_ai_api(prompt)
            return self._parse_ai_response(response)
        except Exception as e:
            print(f"AI analysis failed: {e}")
            # 返回基于规则的回退选择器
            return self._generate_fallback_selectors(html_content, content_type)
    
    def _build_analysis_prompt(self, url: str, html_sample: str, 
                             content_type: ContentType, structure: Dict[str, Any]) -> str:
        """构建AI分析提示"""
        
        content_type_hints = {
            ContentType.ARTICLE: "新闻文章或博客文章",
            ContentType.BLOG: "博客文章",
            ContentType.NEWS: "新闻报道",
            ContentType.RESEARCH: "学术论文或研究报告",
            ContentType.DOCUMENTATION: "技术文档"
        }
        
        hint = content_type_hints.get(content_type, "一般内容")
        
        prompt = f"""
你是一个专业的网页结构分析专家。请分析以下网页的HTML结构，并为抓取{hint}生成CSS选择器。

网页URL: {url}
内容类型: {hint}
页面结构信息: {structure}

HTML样本 (前8000字符):
{html_sample}

请分析页面结构并提供JSON格式的分析结果，包含以下字段：

{{
    "confidence": 0.8,  // 分析置信度 (0-1)
    "selectors": {{
        "title": "CSS选择器",        // 文章标题
        "content": "CSS选择器",      // 主要内容
        "summary": "CSS选择器",      // 摘要/描述
        "author": "CSS选择器",       // 作者
        "publish_date": "CSS选择器", // 发布日期
        "tags": "CSS选择器",         // 标签
        "category": "CSS选择器",     // 分类
        "exclude_selectors": ["CSS选择器数组"]  // 要排除的元素
    }},
    "analysis": {{
        "main_content_area": "描述主要内容区域",
        "navigation_pattern": "导航模式描述",
        "content_structure": "内容结构描述"
    }}
}}

分析要点：
1. 找到最可能包含主要内容的容器
2. 识别标题的层次结构
3. 找到作者、日期等元数据
4. 排除导航、广告、侧边栏等无关内容
5. 考虑页面的响应式设计

请只返回JSON，不要包含其他文本。
"""
        
        return prompt
    
    async def _call_ai_api(self, prompt: str) -> str:
        """调用AI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"AI API error {response.status}: {error_text}")
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            import json
            
            # 移除可能的markdown标记
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            result = json.loads(response)
            
            # 验证结果格式
            if "selectors" not in result:
                result["selectors"] = {}
            if "confidence" not in result:
                result["confidence"] = 0.7
            
            return result
            
        except Exception as e:
            print(f"Failed to parse AI response: {e}")
            return {
                "confidence": 0.5,
                "selectors": {},
                "analysis": {"error": "Failed to parse AI response"}
            }
    
    def _generate_fallback_selectors(self, html_content: str, 
                                   content_type: ContentType) -> Dict[str, Any]:
        """生成回退选择器（基于规则）"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        selectors = {}
        
        # 标题选择器
        title_candidates = ['h1', 'h2', '.title', '.headline', '[itemprop="headline"]']
        for candidate in title_candidates:
            if soup.select(candidate):
                selectors["title"] = candidate
                break
        
        # 内容选择器
        content_candidates = [
            'article', '.content', '.post-content', '.entry-content',
            'main', '.main', '[role="main"]', '.post-body'
        ]
        for candidate in content_candidates:
            if soup.select(candidate):
                selectors["content"] = candidate
                break
        
        # 作者选择器
        author_candidates = [
            '.author', '.by-author', '[itemprop="author"]', 
            '.post-author', '.article-author'
        ]
        for candidate in author_candidates:
            if soup.select(candidate):
                selectors["author"] = candidate
                break
        
        # 日期选择器
        date_candidates = [
            'time', '.date', '.publish-date', '[itemprop="datePublished"]',
            '.post-date', '.article-date'
        ]
        for candidate in date_candidates:
            if soup.select(candidate):
                selectors["publish_date"] = candidate
                break
        
        # 排除元素
        selectors["exclude_selectors"] = [
            'nav', 'header', 'footer', '.sidebar', '.menu', 
            'script', 'style', '.advertisement', '.ads'
        ]
        
        return {
            "confidence": 0.6,
            "selectors": selectors,
            "analysis": {"method": "rule_based_fallback"}
        }
    
    def _validate_selectors(self, soup: BeautifulSoup, 
                          ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和优化选择器"""
        selectors = ai_result.get("selectors", {})
        validated = {}
        confidence_adjustments = []
        
        for field, selector in selectors.items():
            if not selector or field == "exclude_selectors":
                continue
            
            try:
                elements = soup.select(selector)
                if elements:
                    # 检查选择器的质量
                    if len(elements) == 1:
                        confidence_adjustments.append(0.1)  # 唯一选择器更好
                    elif len(elements) <= 3:
                        confidence_adjustments.append(0.05)
                    else:
                        confidence_adjustments.append(-0.1)  # 太多元素可能不准确
                    
                    validated[field] = selector
                else:
                    confidence_adjustments.append(-0.2)  # 无效选择器
            except Exception:
                confidence_adjustments.append(-0.3)  # 语法错误
        
        # 保留排除选择器
        if "exclude_selectors" in selectors:
            validated["exclude_selectors"] = selectors["exclude_selectors"]
        
        # 调整置信度
        base_confidence = ai_result.get("confidence", 0.7)
        adjustment = sum(confidence_adjustments) / max(len(confidence_adjustments), 1)
        final_confidence = max(0.1, min(1.0, base_confidence + adjustment))
        
        return {
            "selectors": validated,
            "confidence": final_confidence
        }
    
    def _generate_selector(self, element) -> str:
        """为元素生成CSS选择器"""
        selectors = []
        
        # 添加标签名
        selectors.append(element.name)
        
        # 添加ID
        if element.get('id'):
            return f"#{element.get('id')}"
        
        # 添加类名
        classes = element.get('class', [])
        if classes:
            class_selector = '.' + '.'.join(classes)
            selectors.append(class_selector)
        
        return selectors[0] if len(selectors) == 1 else ' '.join(selectors)
    
    def _identify_content_patterns(self, soup: BeautifulSoup) -> List[str]:
        """识别内容模式"""
        patterns = []
        
        # 检查常见的内容模式
        if soup.find('article'):
            patterns.append("HTML5语义化文章结构")
        
        if soup.find(attrs={"itemtype": lambda x: x and "schema.org" in x}):
            patterns.append("Schema.org结构化数据")
        
        if soup.find('time'):
            patterns.append("标准时间元素")
        
        if soup.find(attrs={"itemprop": True}):
            patterns.append("微数据标记")
        
        content_divs = soup.find_all('div', class_=lambda x: x and any(
            word in ' '.join(x).lower() for word in ['content', 'article', 'post', 'main']
        ))
        if content_divs:
            patterns.append("基于类名的内容容器")
        
        return patterns
    
    def _generate_recommendations(self, page_info: Dict[str, Any], 
                                structure: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if structure["semantic_elements"]:
            recommendations.append("页面使用了HTML5语义化标签，抓取配置应优先考虑这些元素")
        
        if page_info.get("has_rss"):
            recommendations.append("页面提供RSS源，建议直接使用RSS而非网页抓取")
        
        if structure["media_elements"]["images"] > 10:
            recommendations.append("页面包含大量图片，可能影响加载性能")
        
        if structure["form_elements"]:
            recommendations.append("页面包含表单，可能需要交互或认证")
        
        if not structure["content_containers"]:
            recommendations.append("未发现明显的内容容器，可能需要手动调整选择器")
        
        return recommendations
    
    def _identify_potential_issues(self, soup: BeautifulSoup, url: str) -> List[str]:
        """识别潜在问题"""
        issues = []
        
        # 检查JavaScript依赖
        scripts = soup.find_all('script')
        if len(scripts) > 5:
            issues.append("页面包含大量JavaScript，可能需要渲染")
        
        # 检查动态加载指示
        if soup.find(attrs={"data-lazy": True}) or soup.find(class_=lambda x: x and 'lazy' in ' '.join(x).lower()):
            issues.append("页面使用懒加载，内容可能动态加载")
        
        # 检查验证码
        if soup.find('img', src=lambda x: x and 'captcha' in x.lower()):
            issues.append("页面可能包含验证码")
        
        # 检查登录表单
        login_forms = soup.find_all('form', action=lambda x: x and any(
            word in x.lower() for word in ['login', 'signin', 'auth']
        ))
        if login_forms:
            issues.append("页面可能需要登录")
        
        # 检查单页应用指示
        if soup.find('div', id=lambda x: x and x.lower() in ['root', 'app']):
            issues.append("可能是单页应用(SPA)，需要JavaScript渲染")
        
        return issues
    
    def _check_auth_requirement(self, soup: BeautifulSoup, html_content: str) -> bool:
        """检查是否需要认证"""
        auth_indicators = [
            'login', 'signin', 'authenticate', 'unauthorized',
            '登录', '登陆', '验证', '认证'
        ]
        
        page_text = soup.get_text().lower()
        return any(indicator in page_text for indicator in auth_indicators)
    
    def _check_js_requirement(self, soup: BeautifulSoup) -> bool:
        """检查是否需要JavaScript"""
        # 检查常见的SPA框架
        spa_indicators = ['ng-app', 'data-reactroot', 'vue-app']
        
        for indicator in spa_indicators:
            if soup.find(attrs={indicator: True}) or soup.find(class_=lambda x: x and indicator in ' '.join(x).lower()):
                return True
        
        # 检查大量空的容器
        empty_divs = soup.find_all('div', class_=True)
        empty_count = sum(1 for div in empty_divs if not div.get_text().strip())
        
        return empty_count > len(empty_divs) * 0.3  # 超过30%的div为空
    
    def _estimate_content_quality(self, soup: BeautifulSoup, 
                                structure: Dict[str, Any]) -> float:
        """估计内容质量"""
        score = 0.5  # 基础分数
        
        # 语义化标签加分
        if structure["semantic_elements"]:
            score += 0.2
        
        # 标题结构加分
        if structure["headings"].get("h1", 0) > 0:
            score += 0.1
        
        # 内容容器加分
        if structure["content_containers"]:
            score += 0.15
        
        # 结构化数据加分
        if soup.find(attrs={"itemtype": True}):
            score += 0.1
        
        # 过多脚本减分
        if len(soup.find_all('script')) > 10:
            score -= 0.1
        
        return max(0.0, min(1.0, score))