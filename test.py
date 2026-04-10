import re
from urllib.error import URLError
from urllib.request import Request, urlopen

USER_AGENT = "Mozilla/5.0"
DEFAULT_URL = "https://prts.wiki/w/%E9%BA%A6%E5%93%B2%E4%BC%A6/%E8%AF%AD%E9%9F%B3%E8%AE%B0%E5%BD%95"


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def main() -> None:
    try:
        html = fetch_html(DEFAULT_URL)
    except URLError as e:
        print(f"请求失败: {e}")
        return

    matched = re.search(r'data-voice-key\s*=\s*"([^"]+)"', html)
    if not matched:
        print("未匹配 data-voice-key，页面结构可能已变更")
        return

    print(f"匹配成功: {matched.group(1)}")


if __name__ == "__main__":
    main()
