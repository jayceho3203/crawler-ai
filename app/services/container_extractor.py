import logging
from typing import List, Dict, Optional


logger = logging.getLogger(__name__)


class ContainerExtractor:
    """Extract embedded jobs from a single career page using anchor → container strategy."""

    async def extract(self, career_page_url: str, max_jobs: int) -> List[Dict]:
        try:
            logger.info(f"   🔍 Container extraction for: {career_page_url}")

            from .crawler import crawl_single_url
            result = await crawl_single_url(career_page_url)
            if not result.get('success'):
                return []

            html = result.get('html')
            if not html:
                return []

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            job_indicators = [
                'apply now', 'apply', 'ứng tuyển', 'tuyển dụng',
                'download jd', 'job description', 'mô tả công việc',
                'fulltime', 'part-time', 'toàn thời gian', 'bán thời gian',
                'hạn ứng tuyển', 'deadline', 'thời hạn',
                'mức lương', 'salary', 'lương',
                'nơi làm việc', 'location', 'địa điểm',
                'view details', 'see more', 'learn more', 'join us', 'work with us', 'career opportunity'
            ]

            anchor_elements = []
            for indicator in job_indicators:
                elements = soup.find_all(text=lambda t: t and indicator.lower() in t.lower())
                for element in elements:
                    if element.parent:
                        anchor_elements.append(element.parent)

            containers = []
            for anchor in anchor_elements:
                container = self._find_job_container(anchor)
                if container and container not in containers:
                    containers.append(container)

            jobs: List[Dict] = []
            for idx, container in enumerate(containers[:max_jobs], start=1):
                job_data = self._extract_job_from_container(container, career_page_url, idx)
                if job_data and self._is_valid_job_data(job_data):
                    jobs.append(job_data)

            return jobs
        except Exception as e:
            logger.error(f"   ❌ Container extraction error: {e}")
            return []

    def _find_job_container(self, anchor_element) -> Optional[object]:
        try:
            current = anchor_element
            max_depth = 6
            depth = 0
            while current and depth < max_depth:
                text_content = current.get_text().lower() if hasattr(current, 'get_text') else ''
                indicators = [
                    'fulltime', 'part-time', 'mức lương', 'salary', 'nơi làm việc', 'location',
                    'hạn ứng tuyển', 'deadline', 'apply', 'ứng tuyển'
                ]
                count = sum(1 for i in indicators if i in text_content)
                if count >= 2 and len(current.get_text()) < 2000:
                    return current
                current = current.parent
                depth += 1
            return None
        except Exception:
            return None

    def _extract_job_from_container(self, container, career_page_url: str, job_index: int) -> Dict:
        try:
            text_content = container.get_text()
            title = self._extract_title(container)
            job_type = self._extract_job_type(container)
            location = self._extract_location(container)
            salary = self._extract_salary(container)
            description = text_content.strip()
            company = self._extract_company_from_url(career_page_url)
            job_link = self._extract_job_link(container, career_page_url)

            return {
                'title': title,
                'company': company,
                'location': location,
                'job_type': job_type,
                'salary': salary,
                'description': description,
                'job_link': job_link,
                'source_url': career_page_url,
                'job_index': job_index
            }
        except Exception:
            return {}

    def _extract_title(self, container) -> str:
        try:
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                el = container.find(tag)
                if el:
                    title = el.get_text().strip()
                    if 3 < len(title) < 100:
                        return title
            for cls in ['title', 'job-title', 'position', 'role']:
                el = container.find(class_=lambda x: x and cls in x.lower())
                if el:
                    title = el.get_text().strip()
                    if 3 < len(title) < 100:
                        return title
            strong = container.find('strong')
            if strong:
                title = strong.get_text().strip()
                if 3 < len(title) < 100:
                    return title
            for line in container.get_text().split('\n'):
                line = line.strip()
                if 3 < len(line) < 100:
                    return line
            return ""
        except Exception:
            return ""

    def _extract_job_type(self, container) -> str:
        try:
            text = container.get_text().lower()
            if 'fulltime' in text or 'full-time' in text or 'toàn thời gian' in text:
                return 'Full-time'
            if 'part-time' in text or 'parttime' in text or 'bán thời gian' in text:
                return 'Part-time'
            if 'contract' in text or 'hợp đồng' in text:
                return 'Contract'
            if 'intern' in text or 'thực tập' in text:
                return 'Internship'
            return 'Full-time'
        except Exception:
            return 'Full-time'

    def _extract_location(self, container) -> str:
        try:
            import re
            text = container.get_text()
            patterns = [
                r'nơi làm việc[:\s]+([^\n]+)',
                r'location[:\s]+([^\n]+)',
                r'địa điểm[:\s]+([^\n]+)',
                r'work location[:\s]+([^\n]+)'
            ]
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    loc = m.group(1).strip()
                    if 0 < len(loc) < 100:
                        return loc
            return ""
        except Exception:
            return ""

    def _extract_salary(self, container) -> str:
        try:
            import re
            text = container.get_text()
            patterns = [
                r'mức lương[:\s]+([^\n]+)',
                r'salary[:\s]+([^\n]+)',
                r'lương[:\s]+([^\n]+)'
            ]
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    sal = m.group(1).strip()
                    if 0 < len(sal) < 100:
                        return sal
            return ""
        except Exception:
            return ""

    def _extract_company_from_url(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            domain = domain.replace('www.', '').replace('careers.', '').replace('jobs.', '')
            if '.' in domain:
                return domain.split('.')[0].title()
            return domain.title()
        except Exception:
            return ""

    def _extract_job_link(self, container, career_page_url: str) -> str:
        try:
            links = container.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href and href.startswith('http'):
                    return href
            return career_page_url
        except Exception:
            return career_page_url

    def _is_valid_job_data(self, job_data: Dict) -> bool:
        try:
            title = (job_data.get('title') or '').strip()
            description = (job_data.get('description') or '').strip()
            if len(title) < 3 or len(description) < 20:
                return False
            keywords = [
                'developer', 'engineer', 'analyst', 'manager', 'specialist',
                'consultant', 'coordinator', 'assistant', 'director', 'lead',
                'senior', 'junior', 'intern', 'tester', 'designer', 'architect',
                'marketing', 'sales', 'finance', 'accounting', 'hr'
            ]
            content = f"{title} {description}".lower()
            return any(k in content for k in keywords)
        except Exception:
            return False


