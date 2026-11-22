"""추출 조건과 제외 조건 검증: python -m unittest -v"""

import unittest
from pathlib import Path

from main import (
    COUPON_PATTERN,
    EMAIL_PATTERN,
    GITHUB_PATTERN,
    PHONE_PATTERN,
    STUDENT_PATTERN,
    extract_data,
)


class RegexTest(unittest.TestCase):
    def test_emails_from_sample(self):
        text = "ok@example.com hyunwoo@.ac.kr wrong..name@site.com"
        self.assertEqual(EMAIL_PATTERN.findall(text), ["ok@example.com"])

    def test_emails_do_not_match_invalid_suffixes(self):
        self.assertEqual(EMAIL_PATTERN.findall("abc@example..com a@-bad.com"), [])

    def test_phone_delimiters(self):
        text = "010-1234-5678 010.1234.5678 010 1234 5678 01012345678"
        self.assertEqual(len(PHONE_PATTERN.findall(text)), 4)

    def test_phone_exclusions(self):
        text = "02-1234-5678 063-3290-1114 010-123-4567 010-1234-56789"
        self.assertEqual(PHONE_PATTERN.findall(text), [])

    def test_phone_does_not_extract_part_of_longer_number(self):
        text = "010-1234-5678-99 010-1234-5678a a010-1234-5678"
        self.assertEqual(PHONE_PATTERN.findall(text), [])

    def test_phone_space_extension(self):
        text = "010-1234-5678 99 / 010-5555-6666 010-7777-8888"
        self.assertEqual(
            PHONE_PATTERN.findall(text),
            ["010-5555-6666", "010-7777-8888"],
        )

    def test_student_id_and_department(self):
        text = "[202410512 / 인공지능학과] [999900000 / 외부] [20261122 / 데이터공학과]"
        self.assertEqual(STUDENT_PATTERN.findall(text), [("202410512", "인공지능학과")])

    def test_github_only(self):
        text = "https://github.com/abc/hello http://github.com/xyz/hi.git https://gitlab.com/x/y"
        self.assertEqual(
            GITHUB_PATTERN.findall(text),
            ["https://github.com/abc/hello", "http://github.com/xyz/hi.git"],
        )

    def test_github_trailing_sentence_period(self):
        text = "참고: https://github.com/dawn-coders/campus-mate."
        self.assertEqual(
            GITHUB_PATTERN.findall(text),
            ["https://github.com/dawn-coders/campus-mate"],
        )

    def test_coupon_only_2026_and_exact_4_chars(self):
        text = "FEST-2026-DC01 FEST-2025-OLD9 FEST-2026-123 FEST-2026-ABCDE"
        self.assertEqual(COUPON_PATTERN.findall(text), ["FEST-2026-DC01"])

    def test_real_log_counts_and_total(self):
        text = (Path(__file__).resolve().parent / "festival_log.txt").read_text(encoding="utf-8-sig")
        data = extract_data(text)
        self.assertEqual(len(data["emails"]), 5)
        self.assertEqual(len(data["phones"]), 4)
        self.assertEqual(len(data["students"]), 3)
        self.assertEqual(len(data["github_urls"]), 3)
        self.assertEqual(len(data["coupons"]), 3)
        self.assertEqual(len(data["sales"]), 4)
        self.assertEqual(data["total_sales"], 6_290_500)
        self.assertNotIn("hyunwoo@.ac.kr", data["emails"])
        self.assertNotIn("FEST-2025-OLD9", data["coupons"])

    def test_money_not_double_counted(self):
        text = (
            "2. 정산\n"
            "- A 부스 매출: 1,350,000원 (카드 1,100,000원 / 현금 250,000원)\n"
            "3. 공지\n"
            "- B 부스 매출: 999,999원\n"
        )
        data = extract_data(text)
        self.assertEqual(data["sales"], [("A 부스", 1_350_000)])
        self.assertEqual(data["total_sales"], 1_350_000)


if __name__ == "__main__":
    unittest.main()
