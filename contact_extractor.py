import re
from urllib.parse import urlparse, urljoin, unquote
from typing import List, Dict, Set, Optional

# Constants
SOCIAL_DOMAINS: Set[str] = {
    "linkedin.com", "twitter.com", "facebook.com", "instagram.com",
    "github.com", "gitlab.com", "behance.net", "dribbble.com",
    "medium.com", "stackoverflow.com", "quora.com", "reddit.com",
    "producthunt.com", "angel.co", "crunchbase.com", "dev.to",
    "polywork.com", "toptal.com", "upwork.com", "freelancer.com", "x.com", "tiktok.com", "wa.me"
}

CAREER_KEYWORDS: Set[str] = {
    "career", "job", "hiring", "join us", "work with us", "employment",
    "vacancy", "opportunity", "position", "recruiting", "talent",
    "apply now", "open roles", "we're hiring"
}

# Vietnamese career keywords for better detection
CAREER_KEYWORDS_VI: Set[str] = {
    # Vietnamese keywords (with and without accents, with and without spaces)
    'tuyen-dung', 'tuyển-dụng', 'tuyendung', 'tuyendung',
    'viec-lam', 'việc-làm', 'vieclam', 'vieclam',
    'co-hoi', 'cơ-hội', 'cohoi', 'cohoi',
    'nhan-vien', 'nhân-viên', 'nhanvien', 'nhanvien',
    'tuyen', 'tuyển', 'tuyen', 'tuyen',
    'ung-vien', 'ứng-viên', 'ungvien', 'ungvien',
    'cong-viec', 'công-việc', 'congviec', 'congviec',
    'lam-viec', 'làm-việc', 'lamviec', 'lamviec',
    'moi', 'mời', 'moi', 'moi',
    'thu-viec', 'thử-việc', 'thuviec', 'thuviec',
    'chinh-thuc', 'chính-thức', 'chinhthuc', 'chinhthuc',
    
    # Additional Vietnamese keywords
    'nghe-nghiep', 'nghề-nghiệp', 'nghenghiep', 'nghenghiep',
    'co-hoi-nghe-nghiep', 'cơ-hội-nghề-nghiệp', 'cohoinghenghiep', 'cohoinghenghiep',
    'tim-viec', 'tìm-việc', 'timviec', 'timviec',
    'dang-tuyen', 'đang-tuyển', 'dangtuyen', 'dangtuyen',
    'tuyen-dung-nhan-vien', 'tuyển-dụng-nhân-viên', 'tuyendungnhanvien', 'tuyendungnhanvien',
    'tuyen-dung-developer', 'tuyển-dụng-developer', 'tuyendungdeveloper', 'tuyendungdeveloper',
    'tuyen-dung-engineer', 'tuyển-dụng-engineer', 'tuyendungengineer', 'tuyendungengineer',
    'tuyen-dung-analyst', 'tuyển-dụng-analyst', 'tuyendunganalyst', 'tuyendunganalyst',
    'tuyen-dung-manager', 'tuyển-dụng-manager', 'tuyendungmanager', 'tuyendungmanager',
    'tuyen-dung-designer', 'tuyển-dụng-designer', 'tuyendungdesigner', 'tuyendungdesigner',
    'tuyen-dung-tester', 'tuyển-dụng-tester', 'tuyendungtester', 'tuyendungtester',
    'tuyen-dung-qa', 'tuyển-dụng-qa', 'tuyendungqa', 'tuyendungqa',
    'tuyen-dung-devops', 'tuyển-dụng-devops', 'tuyendungdevops', 'tuyendungdevops',
    'tuyen-dung-data', 'tuyển-dụng-data', 'tuyendungdata', 'tuyendungdata',
    'tuyen-dung-ai', 'tuyển-dụng-ai', 'tuyendungai', 'tuyendungai',
    'tuyen-dung-ml', 'tuyển-dụng-ml', 'tuyendungml', 'tuyendungml',
    'tuyen-dung-ui', 'tuyển-dụng-ui', 'tuyendungui', 'tuyendungui',
    'tuyen-dung-ux', 'tuyển-dụng-ux', 'tuyendungux', 'tuyendungux',
    'tuyen-dung-pm', 'tuyển-dụng-pm', 'tuyendungpm', 'tuyendungpm',
    'tuyen-dung-ba', 'tuyển-dụng-ba', 'tuyendungba', 'tuyendungba',
    'tuyen-dung-scrum', 'tuyển-dụng-scrum', 'tuyendungscrum', 'tuyendungscrum',
    'tuyen-dung-agile', 'tuyển-dụng-agile', 'tuyendungagile', 'tuyendungagile',
    
    # English keywords (with and without hyphens)
    'developer', 'dev', 'programmer', 'engineer',
    'software', 'tech', 'technology', 'it',
    'career', 'job', 'recruitment', 'employment',
    'work', 'position', 'opportunity', 'vacancy',
    'apply', 'application', 'hiring', 'join-us', 'joinus',
    'team', 'talent', 'careers', 'jobs',
    'open-role', 'open-roles', 'openrole', 'openroles',
    'we-are-hiring', 'wearehiring', 'hiring', 'hiring',
    'work-with-us', 'workwithus', 'join-our-team', 'joinourteam',
    'grow-with-us', 'growwithus', 'build-with-us', 'buildwithus',
    'create-with-us', 'createwithus', 'innovate-with-us', 'innovatewithus',
    'full-time', 'fulltime', 'part-time', 'parttime',
    'remote', 'hybrid', 'onsite', 'on-site', 'onsite',
    'freelance', 'contract', 'internship', 'intern',
    'graduate', 'entry-level', 'entrylevel', 'senior',
    'junior', 'lead', 'principal', 'frontend', 'front-end', 'frontend',
    'backend', 'back-end', 'backend', 'fullstack', 'full-stack', 'fullstack',
    'mobile', 'web', 'data', 'ai', 'ml', 'machine-learning', 'machinelearning',
    'devops', 'qa', 'test', 'testing', 'ui', 'ux', 'design', 'product'
}

# Helper functions

def extract_valid_email(email_str: str) -> Optional[str]:
    """
    Validates an email string using a common regex.
    Returns the email if valid, otherwise None.
    """
    if not isinstance(email_str, str):
        return None
    # Basic email regex, can be adjusted for more strictness
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(email_regex, email_str):
        return email_str.lower().strip()
    return None

def extract_embedded_url(href_content: str, base_domain_netloc: Optional[str] = None) -> str:
    """
    Extracts and normalizes an embedded URL from href content.
    Handles cases like '/cdn-cgi/l/email-protection#...'
    """
    # Priority 1: Handle "https://base.com/<https://actual.com>"
    # Find the last occurrence of "<http" which might signify an embedded URL.
    inner_url_start_marker = "<http"
    marker_index = href_content.rfind(inner_url_start_marker)

    if marker_index > 0:  # marker_index > 0 ensures it's not href_content like "<http://...>"
        prefix_part = href_content[:marker_index]  # e.g., "https://gpbullhound.com/"
        parsed_prefix = urlparse(prefix_part)

        # Check if the prefix domain matches the base_domain_netloc
        if parsed_prefix.scheme and parsed_prefix.netloc == base_domain_netloc:
            potential_inner_url_with_bracket = href_content[marker_index:]  # e.g., "<https://...>"
            if potential_inner_url_with_bracket.endswith(">"):
                actual_inner_url = potential_inner_url_with_bracket[1:-1]  # Remove '<' and '>'
                parsed_actual_inner = urlparse(actual_inner_url)
                if parsed_actual_inner.scheme and parsed_actual_inner.netloc:
                    return actual_inner_url  # Successfully extracted inner URL

    # Priority 2: Handle cases like "<https://example.com>" (URL is solely within brackets)
    if href_content.startswith("<") and href_content.endswith(">"):
        url_in_brackets = href_content[1:-1]
        parsed_url_in_brackets = urlparse(url_in_brackets)
        if parsed_url_in_brackets.scheme and parsed_url_in_brackets.netloc:
            return url_in_brackets
    
    # Priority 3: Handle cases like "<http://example.com" (missing closing bracket)
    # This check is for href_content that itself starts with the marker.
    if href_content.startswith(inner_url_start_marker):
        match_angle_bracket_start = re.match(r"<(https?://[^>\s)]+)>?", href_content)
        if match_angle_bracket_start:
            return match_angle_bracket_start.group(1)

    # Priority 4: Handle "https://base.com/https://actual.com" (no angle brackets for inner URL)
    # This is the original script's "Pattern 2"
    positions = [m.start() for m in re.finditer(r'https?://', href_content)]
    if len(positions) > 1:
        for i in range(len(positions) - 1, 0, -1):  # Iterate backwards
            pos = positions[i]
            potential_url = href_content[pos:]
            parsed_potential = urlparse(potential_url)
            if parsed_potential.scheme and parsed_potential.netloc and parsed_potential.netloc != base_domain_netloc:
                # Check if the domain of the prefix part matches base_domain_netloc
                prefix_of_potential_url = href_content[:pos]
                parsed_prefix_of_potential = urlparse(prefix_of_potential_url)
                if parsed_prefix_of_potential.scheme and parsed_prefix_of_potential.netloc == base_domain_netloc:
                    return potential_url
                    
    return href_content # Default: return original content if no specific pattern matched

def normalize_url(url_str: str, base_url: str) -> str:
    parsed_url_obj = urlparse(url_str)
    
    absolute_url = url_str

    if not parsed_url_obj.scheme:
        if not base_url:
            # If no base_url and no scheme, it's likely a malformed or relative path
            # that cannot be resolved without more context.
            # Depending on desired behavior, could return as is, or raise error, or prepend "http://"
            # For now, returning as is, assuming it might be handled later or is an error.
            pass
        else:
            parsed_base = urlparse(base_url)
            # Ensure base_url itself has a scheme, or prepend http to it for joining
            if not parsed_base.scheme:
                # If base_url is like "example.com/path", make it "http://example.com/path"
                # If base_url is like "/some/path" (relative to an unknown domain), this won't make it absolute.
                # This part assumes base_url, if schemeless, is a domain or full path from domain.
                temp_base = f"http://{parsed_base.path}" if not parsed_base.netloc and parsed_base.path else f"http://{parsed_base.netloc}"
                absolute_url = urljoin(temp_base, url_str)
            else:
                absolute_url = urljoin(base_url, url_str)
    
    # Handle URLs that might be percent-encoded
    # Also, unquote can help simplify URLs by decoding %2F to / etc.
    # It's generally safe to unquote path, query, fragment.
    # Re-parse after potential unquoting and scheme addition for consistency
    final_parsed = urlparse(unquote(absolute_url))
    
    # Reconstruct the URL to ensure a consistent format, especially scheme.
    # If scheme is still missing after join (e.g. base_url was just a path), prepend http.
    scheme = final_parsed.scheme if final_parsed.scheme else "http"
    netloc = final_parsed.netloc
    path = final_parsed.path
    query = final_parsed.query
    fragment = final_parsed.fragment # Usually not needed for canonicalization but good to keep if present

    # If netloc is missing but path looks like a domain (e.g. www.example.com/page from a bad join)
    # This is a tricky case. For now, assume urljoin handled it.
    # A more robust solution might try to re-parse path as a potential domain if netloc is empty.

    # Ensure www. is consistently handled (e.g. remove it, or add it - typically remove for canonical)
    # For this function, let's keep it simple and not strip www, as it might be significant for some sites.
    # However, for domain comparison later, stripping www is common.

    return urlparse(f"{scheme}://{netloc}{path}{('?' + query) if query else ''}{('#' + fragment) if fragment else ''}").geturl()


def process_extracted_crawl_results(
    raw_extracted_list: List[Dict[str, str]],
    base_url: str
) -> Dict[str, List[str]]:
    """
    Processes items extracted by a strategy (e.g., RegexExtractionStrategy as label, value pairs)
    to find emails, social links, and career pages.
    """
    classified_contacts: Dict[str, List[str]] = {
        "emails": [],
        "social_links": [],
        "career_pages": [],
    }
    emails_found_raw: Set[str] = set()
    urls_found_raw: Set[str] = set()

    for item in raw_extracted_list:
        label = item.get("label")
        value = item.get("value")
        if not value:  # Skip if no value
            continue

        if label == "email":
            emails_found_raw.add(value)
        elif label == "url":
            urls_found_raw.add(value)

    # Process emails found
    for email_str in emails_found_raw:
        # Assuming extract_valid_email is a helper function available in the scope
        # This function should perform validation and possibly normalization.
        valid_email = extract_valid_email(email_str)
        if valid_email:
            classified_contacts["emails"].append(valid_email)

    # Process URLs found
    unique_social_links: Set[str] = set()
    unique_career_pages: Set[str] = set()

    for url_str in urls_found_raw:
        try:
            normalized_url = normalize_url(url_str, base_url)
            if not normalized_url:  # Skip if normalization failed or returned empty
                continue

            parsed_url = urlparse(normalized_url)
            domain = parsed_url.netloc.lower()
            path_lower = parsed_url.path.lower() if parsed_url.path else ""
            query_lower = parsed_url.query.lower()

            # Check for social links
            # handles cases like "m.facebook.com" or "x.com" (formerly twitter)
            is_social = False
            for social_domain_part in SOCIAL_DOMAINS:
                if social_domain_part == domain or domain.endswith(f".{social_domain_part}"):
                    is_social = True
                    break
            if is_social:
                unique_social_links.add(normalized_url)
                continue  # Prioritize as social, skip career check for this URL

            # Check for career pages
            is_career_candidate = False
            
            # Check both English and Vietnamese keywords
            all_career_keywords = CAREER_KEYWORDS.union(CAREER_KEYWORDS_VI)
            
            for keyword in all_career_keywords:
                # Check keyword in the path or query parameters
                if keyword in path_lower or keyword in query_lower:
                    is_career_candidate = True
                    break
            
            if is_career_candidate:
                # Add heuristic: check for common career path segments to reduce false positives
                career_path_segments = [
                    "career", "jobs", "hiring", "vacancy", "vacancies", "opportunity", "opportunities", 
                    "work-with-us", "join-us", "apply", "recruitment", "careers", "open-roles",
                    "tuyen-dung", "tuyển-dụng", "viec-lam", "việc-làm", "co-hoi", "cơ-hội",
                    "nhan-vien", "nhân-viên", "ung-vien", "ứng-viên", "cong-viec", "công-việc",
                    "lam-viec", "làm-việc", "moi", "mời", "thu-viec", "thử-việc"
                ]
                path_and_query = f"{path_lower}?{query_lower}"

                has_career_segment = False
                for segment in career_path_segments:
                    # Check for segment as a whole word or part of a path/query parameter
                    if f"/{segment}/" in path_and_query or \
                       path_and_query.endswith(f"/{segment}") or \
                       path_and_query.startswith(f"{segment}/") or \
                       f"/{segment}." in path_and_query or \
                       f"_{segment}" in path_and_query or \
                       f"-{segment}" in path_and_query or \
                       f"{segment}=" in path_and_query or \
                       f"&{segment}=" in path_and_query or \
                       f"?{segment}=" in path_and_query or \
                       segment == path_lower.strip('/'): # e.g. /careers
                        has_career_segment = True
                        break
                
                if has_career_segment:
                    unique_career_pages.add(normalized_url)
                # Avoid classifying generic blog posts or news articles that might mention "job"
                # Simpler paths are more likely career pages if keyword matched and not clearly other content type
                elif not any(s in path_lower for s in ["blog", "news", "article", "post", "story", "update", "event"]) and len(path_lower.split('/')) <= 4 :
                    unique_career_pages.add(normalized_url)

        except Exception:
            # Optionally log: print(f"Warning: Could not parse or classify URL '{url_str}': {e}")
            pass

    return {
        "emails": sorted(list(set(classified_contacts["emails"]))), # Ensure uniqueness and sort
        "social_links": sorted(list(unique_social_links)),
        "career_pages": sorted(list(unique_career_pages)),
    }