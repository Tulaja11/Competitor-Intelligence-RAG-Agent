from tavily import TavilyClient
from config import TAVILY_API_KEY, MAX_RESULTS_PER_SEARCH

client = TavilyClient(api_key=TAVILY_API_KEY)

# Each category gets its own search phrasing.
# This is what lets us tag results by intent later.
SEARCH_TEMPLATES = {
    "product": "{name} new product launch announcement",
    "hiring":  "{name} careers job openings hiring",
    "pricing": "{name} pricing plans cost",
}


def fetch_category(competitor, category):
    """Run one Tavily search for a competitor + category."""
    query = SEARCH_TEMPLATES[category].format(name=competitor)
    try:
        response = client.search(
            query=query,
            max_results=MAX_RESULTS_PER_SEARCH,
            search_depth="basic",
        )
    except Exception as e:
        print(f"  [!] {category} search failed: {e}")
        return []

    results = []
    for item in response.get("results", []):
        content = item.get("content", "").strip()
        if not content:
            continue
        results.append({
            "competitor": competitor,
            "category": category,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": content,
        })
    return results


def fetch_competitor(competitor):
    """Fetch all four categories for one competitor."""
    print(f"\nFetching data for: {competitor}")
    all_results = []
    for category in SEARCH_TEMPLATES:
        results = fetch_category(competitor, category)
        print(f"  {category:<8} -> {len(results)} results")
        all_results.extend(results)
    print(f"  Total: {len(all_results)} documents")
    return all_results


if __name__ == "__main__":
    data = fetch_competitor("Notion")
    print("\n--- Sample result ---")
    if data:
        sample = data[0]
        print(f"Category: {sample['category']}")
        print(f"Title:    {sample['title']}")
        print(f"URL:      {sample['url']}")
        print(f"Content:  {sample['content'][:200]}...")