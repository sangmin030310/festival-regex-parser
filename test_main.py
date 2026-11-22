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


    def test_email_allowed_characters_and_multilevel_domain(self):
        text = "user.name+class@jj.ac.kr student_1@sample.co.kr"
        self.assertEqual(
            EMAIL_PATTERN.findall(text),
            ["user.name+class@jj.ac.kr", "student_1@sample.co.kr"],
        )

    def test_email_bad_top_level_domain(self):
        text = "wrong@host.1 wrong@host.a wrong@host..kr good@host.kr"
        self.assertEqual(EMAIL_PATTERN.findall(text), ["good@host.kr"])

    def test_email_near_sentence_punctuation(self):
        text = "문의: help@jj.ac.kr, 응답: staff@sample.org."
        self.assertEqual(
            EMAIL_PATTERN.findall(text),
            ["help@jj.ac.kr", "staff@sample.org"],
        )

    def test_phone_two_numbers_on_one_line(self):
        text = "A 010-1111-2222 B 010 3333 4444 C 010.5555.6666"
        self.assertEqual(
            PHONE_PATTERN.findall(text),
            ["010-1111-2222", "010 3333 4444", "010.5555.6666"],
        )

    def test_phone_rejects_extra_digits_and_letters(self):
        text = "010-1111-22222 010.1111.2222x 1010-1111-2222"
        self.assertEqual(PHONE_PATTERN.findall(text), [])

    def test_student_spaces_and_ten_digits(self):
        text = "[202400001/인공지능학과] [2024000001 / 컴퓨터공학과]"
        self.assertEqual(
            STUDENT_PATTERN.findall(text),
            [("202400001", "인공지능학과")],
        )

    def test_github_links_with_punctuation(self):
        text = "(https://github.com/team1/proj-1), https://github.com/team2/proj2.git."
        self.assertEqual(
            GITHUB_PATTERN.findall(text),
            ["https://github.com/team1/proj-1", "https://github.com/team2/proj2.git"],
        )

    def test_coupon_boundaries(self):
        text = "A-FEST-2026-AB12 FEST-2026-AB123 FEST-2026-AB12!"
        self.assertEqual(COUPON_PATTERN.findall(text), ["FEST-2026-AB12"])

    def test_sales_only_total_not_other_money(self):
        text = (
            "2. 정산\n"
            "- A 부스 매출: 4,000원 (카드 3,000원 / 현금 1,000원)\n"
            "- B 부스 매출: 12,500원 (쿠폰 5,000원)\n"
            "3. 공지\n"
        )
        data = extract_data(text)
        self.assertEqual(data["sales"], [("A 부스", 4000), ("B 부스", 12500)])
        self.assertEqual(data["total_sales"], 16500)

    def test_no_sales_section(self):
        text = "1. 참가자\n- A 부스 매출: 100,000원\n3. 공지\n"
        self.assertEqual(extract_data(text)["total_sales"], 0)

    def test_real_log_exact_result_values(self):
        text = (Path(__file__).resolve().parent / "festival_log.txt").read_text(encoding="utf-8-sig")
        data = extract_data(text)
        self.assertEqual(data["students"], [
            ("202410512", "인공지능학과"),
            ("202521088", "컴퓨터공학과"),
            ("202230415", "전자전기공학부"),
        ])
        self.assertEqual(data["coupons"], [
            "FEST-2026-DC01", "FEST-2026-BH99", "FEST-2026-GP77",
        ])
        self.assertEqual(data["sales"], [
            ("타코야끼 푸드트럭", 1350000),
            ("불초밥 & 닭꼬치 부스", 2180500),
            ("수제 추로스 & 에이드", 840000),
            ("공과대학 학생회 주점", 1920000),
        ])


if __name__ == "__main__":
    unittest.main()
