# app/utils/constants.py
"""
Constants and configuration for the crawler application
Enhanced with strict filtering constants
"""

# Vietnamese software company career keywords
CAREER_KEYWORDS_VI = [
    # Vietnamese keywords (with and without accents, with and without spaces, no duplicates)
    'tuyen-dung', 'tuyển-dụng', 'tuyendung',
    'viec-lam', 'việc-làm', 'vieclam',
    'co-hoi', 'cơ-hội', 'cohoi',
    'nhan-vien', 'nhân-viên', 'nhanvien',
    'tuyen', 'tuyển',
    'ung-vien', 'ứng-viên', 'ungvien',
    'cong-viec', 'công-việc', 'congviec',
    'lam-viec', 'làm-việc', 'lamviec',
    'moi', 'mời',
    'thu-viec', 'thử-việc', 'thuviec',
    'chinh-thuc', 'chính-thức', 'chinhthuc',
    'nghe-nghiep', 'nghề-nghiệp', 'nghenghiep',
    'co-hoi-nghe-nghiep', 'cơ-hội-nghề-nghiệp', 'cohoinghenghiep',
    'tim-viec', 'tìm-việc', 'timviec',
    'dang-tuyen', 'đang-tuyển', 'dangtuyen',
    'tuyen-dung-nhan-vien', 'tuyển-dụng-nhân-viên', 'tuyendungnhanvien',
    'tuyen-dung-developer', 'tuyển-dụng-developer', 'tuyendungdeveloper',
    'tuyen-dung-engineer', 'tuyển-dụng-engineer', 'tuyendungengineer',
    'tuyen-dung-analyst', 'tuyển-dụng-analyst', 'tuyendunganalyst',
    'tuyen-dung-manager', 'tuyển-dụng-manager', 'tuyendungmanager',
    'tuyen-dung-designer', 'tuyển-dụng-designer', 'tuyendungdesigner',
    'tuyen-dung-tester', 'tuyển-dụng-tester', 'tuyendungtester',
    'tuyen-dung-qa', 'tuyển-dụng-qa', 'tuyendungqa',
    'tuyen-dung-devops', 'tuyển-dụng-devops', 'tuyendungdevops',
    'tuyen-dung-data', 'tuyển-dụng-data', 'tuyendungdata',
    'tuyen-dung-ai', 'tuyển-dụng-ai', 'tuyendungai',
    'tuyen-dung-ml', 'tuyển-dụng-ml', 'tuyendungml',
    'tuyen-dung-ui', 'tuyển-dụng-ui', 'tuyendungui',
    'tuyen-dung-ux', 'tuyển-dụng-ux', 'tuyendungux',
    'tuyen-dung-pm', 'tuyển-dụng-pm', 'tuyendungpm',
    'tuyen-dung-ba', 'tuyển-dụng-ba', 'tuyendungba',
    'tuyen-dung-scrum', 'tuyển-dụng-scrum', 'tuyendungscrum',
    'tuyen-dung-agile', 'tuyển-dụng-agile', 'tuyendungagile',
    # English keywords (no duplicates)
    'developer', 'dev', 'programmer', 'engineer',
    'software', 'tech', 'technology', 'it',
    'career', 'job', 'recruitment', 'employment',
    'work', 'position', 'opportunity', 'vacancy',
    'apply', 'application', 'hiring', 'join-us',
    'team', 'talent', 'careers', 'jobs',
    'open-role', 'open-roles', 'we-are-hiring',
    'work-with-us', 'join-our-team', 'grow-with-us',
    'build-with-us', 'create-with-us', 'innovate-with-us',
    'full-time', 'part-time', 'remote', 'hybrid',
    'onsite', 'on-site', 'freelance', 'contract',
    'internship', 'intern', 'graduate', 'entry-level',
    'senior', 'junior', 'lead', 'principal',
    'frontend', 'front-end', 'backend', 'back-end',
    'fullstack', 'full-stack', 'mobile', 'web',
    'data', 'ai', 'ml', 'machine-learning',
    'devops', 'qa', 'test', 'testing',
    'ui', 'ux', 'design', 'product'
]

# Job-specific keywords for detailed job link detection
JOB_KEYWORDS_DETAILED = [
    # Job titles and roles
    'developer', 'dev', 'engineer', 'programmer', 'analyst',
    'designer', 'manager', 'lead', 'architect', 'consultant',
    'specialist', 'coordinator', 'assistant', 'director',
    'frontend', 'backend', 'fullstack', 'mobile', 'web',
    'data', 'ai', 'ml', 'devops', 'qa', 'test',
    'ui', 'ux', 'product', 'business', 'marketing',
    'sales', 'customer', 'support', 'admin', 'hr',
    
    # Job-related actions
    'apply', 'application', 'submit', 'join', 'work',
    'position', 'role', 'opportunity', 'vacancy', 'opening',
    'career', 'job', 'employment', 'hiring', 'recruitment',
    
    # Vietnamese job terms
    'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí', 'công việc',
    'ứng tuyển', 'nộp đơn', 'tham gia', 'làm việc',
    'nghề nghiệp', 'ngành nghề', 'chuyên môn'
]

# Common job board platforms
JOB_BOARD_DOMAINS = {
    'topcv.vn', 'careerbuilder.vn', 'jobstreet.vn', 'vietnamworks.com',
    'mywork.com.vn', '123job.vn', 'timviec365.vn', 'careerlink.vn',
    'indeed.com', 'linkedin.com/jobs', 'glassdoor.com', 'monster.com',
    'ziprecruiter.com', 'simplyhired.com', 'dice.com', 'angel.co',
    'stackoverflow.com/jobs', 'github.com/jobs', 'remote.co', 'weworkremotely.com'
}

# Software company career selectors
CAREER_SELECTORS = [
    'a[href*="tuyen-dung"]', 'a[href*="viec-lam"]',
    'a[href*="career"]', 'a[href*="job"]',
    'a[href*="recruitment"]', 'a[href*="employment"]',
    'a[href*="developer"]', 'a[href*="dev"]',
    'a[href*="software"]', 'a[href*="tech"]',
    'a[href*="hiring"]', 'a[href*="join-us"]',
    'a[href*="talent"]', 'a[href*="team"]',
    'a[href*="apply"]', 'a[href*="position"]',
    'a[href*="vacancy"]', 'a[href*="opportunity"]',
    'a[href*="open-role"]', 'a[href*="open-roles"]',
    'a[href*="we-are-hiring"]', 'a[href*="work-with-us"]',
    '.menu a', '.nav a', 'header a', 'footer a',
    'nav a', '.navigation a', '.navbar a',
    '.careers a', '.jobs a', '.team a',
    '.career a', '.job a', '.hiring a',
    '.recruitment a', '.talent a', '.apply a'
]

# Enhanced job link selectors for detailed detection
JOB_LINK_SELECTORS = [
    # Direct job links
    'a[href*="/job/"]', 'a[href*="/jobs/"]', 'a[href*="/position/"]',
    'a[href*="/career/"]', 'a[href*="/opportunity/"]', 'a[href*="/vacancy/"]',
    'a[href*="/apply/"]', 'a[href*="/application/"]',
    'a[href*="/tuyen-dung/"]', 'a[href*="/viec-lam/"]', 'a[href*="/co-hoi/"]',
    
    # Job-related classes
    '.job a', '.career a', '.position a', '.opportunity a',
    '.vacancy a', '.apply a', '.application a',
    '.job-item a', '.career-item a', '.position-item a',
    '.job-card a', '.career-card a', '.position-card a',
    
    # Generic selectors with job context
    'article a', '.card a', '.item a', '.listing a',
    '.post a', '.entry a', '.content a',
    
    # Navigation and menu links
    '.nav a', '.menu a', '.navigation a', '.navbar a',
    'nav a', 'header a', 'footer a',
    
    # Button and action links
    '.btn a', '.button a', '.action a', '.cta a',
    'button a', '[role="button"] a'
]

# Cache configuration
CACHE_DURATION = 3600  # 1 hour

# Crawling configuration
DEFAULT_TIMEOUT = 60000  # 60 seconds thay vì 30
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
DEFAULT_HEADERS = {
    'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Strong non-career indicators for filtering
STRONG_NON_CAREER_INDICATORS = [
    # Content types
    'blog', 'news', 'article', 'post', 'story', 'tin-tuc', 'tin', 'bai-viet',
    'whitepaper', 'ebook', 'ebooks', 'guide', 'tutorial', 'manual', 'documentation',
    'case-study', 'case-studies', 'success-story', 'testimonial', 'review',
    'press', 'media', 'publication', 'research', 'analysis', 'report',
    
    # Business pages
    'product', 'products', 'service', 'services', 'solution', 'solutions',
    'about', 'contact', 'company', 'team', 'leadership', 'investor',
    'partnership', 'partners', 'client', 'customer', 'enterprise',
    'industry', 'market', 'business', 'commercial', 'trade',
    
    # Technical/Development
    'technology', 'tech', 'digital', 'transformation', 'implementation',
    'deployment', 'development', 'deploy', 'successfully', 'application',
    'software', 'platform', 'system', 'infrastructure', 'architecture',
    'api', 'sdk', 'framework', 'library', 'tool', 'tools',
    
    # Events and Training
    'webinar', 'conference', 'workshop', 'training', 'certification',
    'event', 'events', 'seminar', 'meetup', 'summit', 'forum',
    'award', 'recognition', 'milestone', 'achievement', 'celebration',
    
    # User/Account pages
    'login', 'register', 'signup', 'signin', 'account', 'profile',
    'dashboard', 'panel', 'admin', 'control', 'manage', 'settings',
    'user', 'member', 'community', 'forum', 'support', 'help',
    
    # E-commerce
    'cart', 'checkout', 'payment', 'order', 'purchase', 'buy', 'shop',
    'store', 'marketplace', 'pricing', 'price', 'cost', 'fee',
    
    # Navigation/Utility
    'home', 'main', 'index', 'search', 'filter', 'sort', 'category',
    'tag', 'author', 'privacy', 'terms', 'policy', 'legal',
    'sitemap', 'rss', 'feed', 'subscribe', 'newsletter',
    
    # Vietnamese specific
    'doanh-nghiep', 'khach-hang', 'doi-tac', 'san-pham', 'dich-vu',
    'giai-phap', 'cong-nghe', 'chuyen-gia', 'kinh-nghiem', 'du-an',
    'nghien-cuu', 'phan-tich', 'bao-cao', 'tai-lieu', 'huong-dan',
    'thanh-cong', 'danh-gia', 'nhan-xet', 'cam-nhan', 'chia-se',
    'su-kien', 'hoi-thao', 'dao-tao', 'chung-chi', 'giai-thuong',
    'dang-nhap', 'dang-ky', 'tai-khoan', 'quan-ly', 'cai-dat',
    'gio-hang', 'thanh-toan', 'dat-hang', 'mua-hang', 'cua-hang',
    'trang-chu', 'tim-kiem', 'danh-muc', 'the', 'tac-gia',
    'quyen-rieng-tu', 'dieu-khoan', 'chinh-sach', 'phap-ly'
]

# Strong non-job indicators for job link filtering
STRONG_NON_JOB_INDICATORS = [
    'blog', 'news', 'article', 'post', 'story', 'product', 'service', 'solution',
    'about', 'contact', 'home', 'main', 'index', 'dashboard', 'profile',
    'login', 'register', 'signup', 'signin', 'account', 'settings',
    'cart', 'checkout', 'payment', 'order', 'purchase', 'buy',
    'search', 'filter', 'sort', 'category', 'tag', 'author', 'user',
    'admin', 'panel', 'control', 'manage', 'edit', 'delete', 'create'
]

# Career exact path patterns (ONLY career listing pages, not job detail pages)
CAREER_EXACT_PATTERNS = [
    '/tuyen-dung', '/tuyển-dụng', '/tuyendung',
    '/viec-lam', '/việc-làm', '/vieclam',
    '/co-hoi', '/cơ-hội', '/cohoi',
    '/nhan-vien', '/nhân-viên', '/nhanvien',
    '/ung-vien', '/ứng-viên', '/ungvien',
    '/cong-viec', '/công-việc', '/congviec',
    '/lam-viec', '/làm-việc', '/lamviec',
    '/moi', '/mời',
    '/thu-viec', '/thử-việc', '/thuviec',
    '/chinh-thuc', '/chính-thức', '/chinhthuc',
    '/nghe-nghiep', '/nghề-nghiệp', '/nghenghiep',
    '/co-hoi-nghe-nghiep', '/cơ-hội-nghề-nghiệp', '/cohoinghenghiep',
    '/tim-viec', '/tìm-việc', '/timviec',
    '/dang-tuyen', '/đang-tuyển', '/dangtuyen',
    '/career', '/careers', '/job', '/jobs', '/hiring', '/recruitment',
    '/employment', '/vacancy', '/vacancies', '/opportunity', '/opportunities',
    '/position', '/positions', '/apply', '/application', '/applications',
    '/join-us', '/joinus', '/work-with-us', '/workwithus',
    '/open-role', '/open-roles', '/openrole', '/openroles',
    '/we-are-hiring', '/wearehiring', '/talent', '/team'
]

# Job exact path patterns for detailed job link detection
JOB_EXACT_PATTERNS = [
    '/job/', '/jobs/', '/position/', '/positions/',
    '/career/', '/careers/', '/opportunity/', '/opportunities/',
    '/vacancy/', '/vacancies/', '/opening/', '/openings/',
    '/apply/', '/application/', '/applications/',
    '/tuyen-dung/', '/tuyển-dụng/', '/tuyendung/',
    '/viec-lam/', '/việc-làm/', '/vieclam/',
    '/co-hoi/', '/cơ-hội/', '/cohoi/',
    '/nhan-vien/', '/nhân-viên/', '/nhanvien/',
    '/ung-vien/', '/ứng-viên/', '/ungvien/',
    '/cong-viec/', '/công-việc/', '/congviec/',
    '/lam-viec/', '/làm-việc/', '/lamviec/'
]

# Scoring thresholds for strict filtering
CAREER_SCORE_THRESHOLD = 8  # Tăng từ 6 lên 8 - Minimum score for career page acceptance
JOB_LINK_SCORE_THRESHOLD = 6  # Tăng từ 5 lên 6 - Minimum score for job link acceptance
CAREER_CONTENT_VALIDATION_THRESHOLD = 3  # Tăng từ 2 lên 3 - Minimum career text indicators for content validation
JOB_CONTENT_VALIDATION_THRESHOLD = 3  # Tăng từ 2 lên 3 - Minimum job text indicators for content validation

# Path depth limits
MAX_CAREER_PATH_DEPTH = 2  # Giảm từ 4 xuống 2 - Maximum path depth for career pages
MAX_JOB_PATH_DEPTH = 3  # Giảm từ 5 xuống 3 - Maximum path depth for job links

# File extensions to reject
REJECTED_FILE_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.zip',
    '.rar', '.7z', '.tar', '.gz', '.exe', '.dmg', '.pkg'
]

# Date patterns to reject
REJECTED_DATE_PATTERNS = [
    r'/\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
    r'/\d{4}/\d{1,2}',  # YYYY/MM
    r'/\d{1,2}/\d{4}',  # MM/YYYY
    r'/\d{4}-\d{1,2}',  # YYYY-MM
    r'/\d{1,2}-\d{4}'   # MM-YYYY
]

# ID patterns to reject
REJECTED_ID_PATTERNS = [
    r'/[a-f0-9]{8,}',  # Long hex IDs
    r'/\d{5,}',  # Long numeric IDs
    r'/[a-z0-9]{10,}',  # Long alphanumeric IDs
    r'/[a-f0-9]{4,}',  # Medium hex IDs
    r'/\d{3,}',  # Medium numeric IDs
]

# Non-career path patterns to reject
REJECTED_NON_CAREER_PATHS = [
    '/services/', '/service/', '/solutions/', '/solution/',
    '/products/', '/product/', '/industries/', '/industry/',
    '/about/', '/contact/', '/blog/', '/news/', '/article/',
    '/admin/', '/login/', '/register/', '/signup/', '/signin/',
    '/cart/', '/checkout/', '/payment/', '/order/', '/purchase/',
    '/search/', '/filter/', '/sort/', '/category/', '/tag/',
    '/author/', '/user/', '/profile/', '/account/', '/settings/',
    '/panel/', '/control/', '/manage/', '/edit/', '/delete/', '/create/',
    '/dashboard', '/member', '/page', '/item', '/detail', '/view', '/show'
] 