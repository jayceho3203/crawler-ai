import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.upwork.com/freelance-jobs/apply/Senior-Mobile-Developer_~021886899760086957583/",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main()) 