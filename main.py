"""2026 전주대학교 대동제·해커톤 로그 정규표현식 분석 프로그램.

사용법:
    python main.py
    python main.py 다른_로그.txt

파이썬 표준 라이브러리만 사용합니다.
"""

import argparse
import re
from pathlib import Path


# 1. 이메일: 아이디 중간의 점은 허용, 연속 점이나 손상된 도메인은 제외
# 마지막 도메인은 알파벳 2자리 이상으로 제한한다 (예: .kr, .com).
EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}"
    r"(?![A-Za-z0-9_-]|\.(?!\s|$|[)\]\"']))"
)

# 2. 추가 숫자 구간은 제외하되, 공백 뒤에 다른 정상 번호가 나오면 각각 추출
PHONE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])010[-. ]?\d{4}[-. ]?\d{4}"
    r"(?![A-Za-z0-9]|[-.]\d|[ \t](?!010(?:[-. ]?\d{4}){2}\b)\d)"
)

# 3. [202로 시작하는 정확히 9자리 학번 / 학과명]
STUDENT_PATTERN = re.compile(r"\[(202\d{6})[ \t]*/[ \t]*([^\]\r\n/]+?)[ \t]*\]")

# 4-1. GitLab이 아닌 GitHub 저장소(소유자/저장소명), http와 https 허용
GITHUB_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]*[A-Za-z0-9_-]"
    r"(?=$|[\s)\]>\"',.!;:])"
)

# 4-2. FEST-2026-XXXX: 끝 4자리는 영문 대문자 또는 숫자
COUPON_PATTERN = re.compile(r"(?<![A-Za-z0-9-])FEST-2026-[A-Z0-9]{4}(?![A-Za-z0-9-])")

# 5. '매출:' 바로 뒤의 금액만 포착, 카드·현금·쿠폰 금액은 합산하지 않음
SALES_PATTERN = re.compile(
    r"^[ \t]*-[ \t]*(?P<booth>[^\r\n]+?)[ \t]+매출:[ \t]*"
    r"(?P<amount>\d{1,3}(?:,\d{3})*|\d+)원",
    re.MULTILINE,
)


def extract_data(text: str) -> dict:
    """로그에서 과제의 5가지 항목을 추출해 사전으로 반환합니다."""
    emails = EMAIL_PATTERN.findall(text)
    phones = PHONE_PATTERN.findall(text)
    students = [
        (student_id, department.strip())
        for student_id, department in STUDENT_PATTERN.findall(text)
    ]
    github_urls = GITHUB_PATTERN.findall(text)
    coupons = COUPON_PATTERN.findall(text)

    # 정산 섹션(2번)만 분석하여 다른 섹션의 금액이 끼어들지 않게 함
    section = re.search(r"^2\..*?(?=^3\.|\Z)", text, re.MULTILINE | re.DOTALL)
    sales_text = section.group(0) if section else ""
    sales = [
        (match.group("booth").strip(), int(match.group("amount").replace(",", "")))
        for match in SALES_PATTERN.finditer(sales_text)
    ]

    return {
        "emails": emails,
        "phones": phones,
        "students": students,
        "github_urls": github_urls,
        "coupons": coupons,
        "sales": sales,
        "total_sales": sum(amount for _, amount in sales),
    }


def print_results(data: dict) -> None:
    """추출 결과와 매출 합계를 과제 번호에 맞춰 출력합니다."""
    sections = [
        ("1. 유효한 이메일", data["emails"]),
        ("2. 010 휴대폰 번호", data["phones"]),
        ("3. 재학생 학번·학과 (튜플)", data["students"]),
        ("4-1. GitHub 저장소 URL", data["github_urls"]),
        ("4-2. 2026년 유효 쿠폰", data["coupons"]),
    ]

    for title, values in sections:
        print(f"\n{title} — {len(values)}개")
        for value in values:
            print(f"  {value}")

    print(f"\n5. 부스별 총매출 — {len(data['sales'])}개")
    for booth, amount in data["sales"]:
        print(f"  {booth}: {amount:,}원")
    print(f"전체 매출 합계: {data['total_sales']:,}원")


def main() -> None:
    parser = argparse.ArgumentParser(description="전주대 축제·해커톤 로그 정규표현식 분석")
    parser.add_argument(
        "log_file", nargs="?", type=Path,
        default=Path(__file__).resolve().parent / "festival_log.txt",
        help="분석할 TXT 파일(생략 시 현재 과제 로그 사용)",
    )
    args = parser.parse_args()

    try:
        text = args.log_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        parser.exit(1, f"로그 파일을 읽을 수 없습니다: {args.log_file}\n오류: {exc}\n")

    print_results(extract_data(text))


if __name__ == "__main__":
    main()
