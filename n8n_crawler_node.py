from n8n import NodeBase, NodeExecutionError
from crawl4ai import AsyncWebCrawler
import asyncio

class WebCrawlerNode(NodeBase):
    async def execute(self):
        try:
            url = self.get_input_data('url')
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                
                return {
                    'markdown': result.markdown,
                    'html': result.html,
                    'text': result.text
                }
                
        except Exception as e:
            raise NodeExecutionError(f"Web crawling failed: {str(e)}")

    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to crawl"
                }
            },
            "required": ["url"]
        }

    def get_output_schema(self):
        return {
            "type": "object",
            "properties": {
                "markdown": {"type": "string"},
                "html": {"type": "string"},
                "text": {"type": "string"}
            }
        } 