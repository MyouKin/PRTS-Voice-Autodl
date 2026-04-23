import re
import time
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
VOICE_CODES = {
    1: "voice",
    2: "voice_cn",
    3: "voice_kr",
    4: "voice_en",
    5: "voice_custom",
}


def http_get_bytes(url: str, timeout: int = 20) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_text(url: str, timeout: int = 20) -> str:
    return http_get_bytes(url, timeout=timeout).decode("utf-8", errors="ignore")


def get_voice_key(page_html: str) -> Optional[str]:
    # PRTS 页面上常见格式: data-voice-key="char_123_xxx"
    match = re.search(r'data-voice-key\s*=\s*"([^"]+)"', page_html)
    return match.group(1) if match else None


def build_wiki_url(character_name: str) -> str:
    return f"https://prts.wiki/w/{quote(character_name)}/{quote('语音记录')}"


def download_voice_files(
    voice_code: str,
    voice_key: str,
    output_prefix: str,
    max_index: int = 200,
    max_consecutive_misses: int = 12,
) -> int:
    saved = 0
    misses = 0
    output_dir = Path.cwd()

    for i in range(1, max_index + 1):
        seq = f"{i:03d}"
        file_url = f"https://static.prts.wiki/{voice_code}/{voice_key}/CN_{seq}.wav"
        filename = output_dir / f"{output_prefix}-{seq}.wav"

        try:
            data = http_get_bytes(file_url)
            filename.write_bytes(data)
            print(f"[OK] {filename.name}")
            saved += 1
            misses = 0
            time.sleep(0.2)
        except HTTPError as e:
            if e.code == 404:
                misses += 1
                print(f"[404] {file_url}")
                if misses >= max_consecutive_misses and saved > 0:
                    print("连续缺失较多，提前结束下载。")
                    break
            else:
                print(f"[HTTP {e.code}] {file_url}")
                misses += 1
        except URLError as e:
            print(f"[网络错误] {file_url} -> {e}")
            misses += 1

    return saved


def main() -> None:
    character = input("请输入干员中文名称，例如麦哲伦\n").strip()
    wiki_url = build_wiki_url(character)

    try:
        lan = int(
            input(
                "输入语言选项：\n"
                "(1)日语 voice\n"
                "(2)汉语 voice_cn\n"
                "(3)韩语 voice_kr\n"
                "(4)英语 voice_en\n"
                "(5)特殊语言 voice_custom\n"
            )
        )
    except ValueError:
        print("语言选项必须是数字。")
        return

    if lan not in VOICE_CODES:
        print("错误：语言选项超出范围。")
        return

    output_name = input("输入生成文件的角色名称（建议英文/拼音）\n").strip()
    if not output_name:
        print("输出名称不能为空。")
        return

    print(f"正在读取页面：{wiki_url}")
    try:
        page_html = fetch_text(wiki_url)
    except Exception as e:  # noqa: BLE001
        print(f"读取页面失败：{e}")
        return

    voice_key = get_voice_key(page_html)
    if not voice_key:
        print("未找到 data-voice-key，页面结构可能已变化。")
        return

    print(f"识别到角色代码：{voice_key}")
    downloaded = download_voice_files(
        voice_code=VOICE_CODES[lan],
        voice_key=voice_key,
        output_prefix=output_name,
    )
    print(f"下载完成，共保存 {downloaded} 个文件。")


if __name__ == "__main__":
    main()
