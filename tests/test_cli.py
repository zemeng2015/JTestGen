import unittest

from javatestgen.cli import build_parser


class CliTests(unittest.TestCase):
    def test_parser_supports_doctor_command(self) -> None:
        args = build_parser().parse_args(["doctor", "."])

        self.assertEqual(args.command, "doctor")

    def test_parser_supports_scan_command(self) -> None:
        args = build_parser().parse_args(["scan", ".", "--top", "3", "--skip-verify"])

        self.assertEqual(args.command, "scan")
        self.assertEqual(args.top, 3)
        self.assertTrue(args.skip_verify)


if __name__ == "__main__":
    unittest.main()
